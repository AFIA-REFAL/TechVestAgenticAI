const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Serve the HTML file using file:// protocol
  const filePath = 'file://' + path.resolve(__dirname, 'index.html');

  async function loadPage() {
    await page.goto(filePath);
    await page.waitForSelector('#firstName');
    return {
      firstName: await page.$('#firstName'),
      lastName: await page.$('#lastName'),
      email: await page.$('#email'),
      phone: await page.$('#phone'),
      password: await page.$('#password'),
      confirmPassword: await page.$('#confirmPassword'),
      registerBtn: await page.$('#registerBtn'),
    };
  }

  // ============ TEST 1: Verify all fields are present ============
  let els = await loadPage();
  if (els.firstName && els.lastName && els.email && els.phone && els.password && els.confirmPassword && els.registerBtn) {
    console.log('✅ TEST 1 PASSED: All form fields and submit button are present');
  } else {
    console.log('❌ TEST 1 FAILED: Some form fields are missing');
  }

  // ============ TEST 2: Empty form submission - should fail validation ============
  await els.firstName.click();
  await els.firstName.fill('a');
  await els.firstName.fill('');
  await els.registerBtn.click();
  await page.waitForTimeout(500);

  const firstNameError = await page.$('#firstNameError');
  const isErrorVisible = await firstNameError.evaluate(el => el.classList.contains('visible'));

  if (isErrorVisible) {
    console.log('✅ TEST 2 PASSED: Empty form shows validation errors');
  } else {
    console.log('❌ TEST 2 FAILED: Empty form did not show validation errors');
  }

  // ============ TEST 3: Invalid email validation ============
  els = await loadPage();

  await els.firstName.fill('John');
  await els.lastName.fill('Doe');
  await els.email.fill('invalid-email');
  await els.password.fill('Test1234');
  await els.confirmPassword.fill('Test1234');
  await page.waitForTimeout(500);

  const emailEl = await page.$('#email');
  const hasEmailError = await emailEl.evaluate(el => el.classList.contains('error'));
  const emailErrorMsg = await page.$('#emailError');
  const emailErrorVisible = await emailErrorMsg.evaluate(el => el.classList.contains('visible'));

  if (hasEmailError && emailErrorVisible) {
    console.log('✅ TEST 3 PASSED: Invalid email shows validation error');
  } else {
    console.log('❌ TEST 3 FAILED: Invalid email did not show validation error');
  }

  // ============ TEST 4: Password mismatch validation ============
  await els.email.fill('john@example.com');
  await els.password.fill('Test1234');
  await els.confirmPassword.fill('DifferentPass');
  await page.waitForTimeout(500);

  const confirmEl = await page.$('#confirmPassword');
  const hasConfirmError = await confirmEl.evaluate(el => el.classList.contains('error'));
  const confirmErrorMsg = await page.$('#confirmError');
  const confirmErrorVisible = await confirmErrorMsg.evaluate(el => el.classList.contains('visible'));

  if (hasConfirmError && confirmErrorVisible) {
    console.log('✅ TEST 4 PASSED: Password mismatch shows error');
  } else {
    console.log('❌ TEST 4 FAILED: Password mismatch did not show error');
  }

  // ============ TEST 5: Successful registration ============
  await els.confirmPassword.fill('Test1234');
  await page.waitForTimeout(500);
  await els.registerBtn.click();
  await page.waitForTimeout(500);

  const successMsg = await page.$('#successMessage');
  const isSuccessVisible = await successMsg.evaluate(el => el.classList.contains('visible'));

  if (isSuccessVisible) {
    console.log('✅ TEST 5 PASSED: Successful registration shows success message');
  } else {
    console.log('❌ TEST 5 FAILED: Successful registration did not show success message');
  }

  // ============ TEST 6: Password strength indicator ============
  els = await loadPage();

  // Weak password
  await els.password.fill('short');
  await page.waitForTimeout(300);
  const weakBar = await page.$('#passwordStrengthBar.weak');
  if (weakBar) {
    console.log('✅ TEST 6a PASSED: Weak password shows weak strength indicator');
  } else {
    console.log('❌ TEST 6a FAILED: Weak password did not show weak indicator');
  }

  // Strong password
  await els.password.fill('Str0ng!Pass#123');
  await page.waitForTimeout(300);
  const strongBar = await page.$('#passwordStrengthBar.strong');
  if (strongBar) {
    console.log('✅ TEST 6b PASSED: Strong password shows strong strength indicator');
  } else {
    console.log('❌ TEST 6b FAILED: Strong password did not show strong indicator');
  }

  // ============ TEST 7: Phone number validation ============
  await els.phone.fill('abc');
  await page.waitForTimeout(300);
  const phoneEl = await page.$('#phone');
  const phoneError = await phoneEl.evaluate(el => el.classList.contains('error'));
  if (phoneError) {
    console.log('✅ TEST 7a PASSED: Invalid phone shows error');
  } else {
    console.log('❌ TEST 7a FAILED: Invalid phone did not show error');
  }

  await els.phone.fill('+1 (555) 123-4567');
  await page.waitForTimeout(300);
  const phoneSuccess = await phoneEl.evaluate(el => el.classList.contains('success'));
  if (phoneSuccess) {
    console.log('✅ TEST 7b PASSED: Valid phone passes validation');
  } else {
    console.log('❌ TEST 7b FAILED: Valid phone did not pass validation');
  }

  // ============ TEST 8: Page title check ============
  const title = await page.title();
  if (title === 'Registration Page') {
    console.log('✅ TEST 8 PASSED: Page title is correct');
  } else {
    console.log('❌ TEST 8 FAILED: Page title is incorrect - got "' + title + '"');
  }

  await browser.close();
  console.log('\n🏁 All tests completed!');
})().catch(err => {
  console.error('❌ Test execution failed:', err.message);
  process.exit(1);
});
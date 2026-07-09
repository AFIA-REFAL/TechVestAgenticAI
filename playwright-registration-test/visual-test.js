const { chromium } = require('playwright');
const path = require('path');

(async () => {
  // Launch browser in VISIBLE mode (non-headless) with a slow motion to see actions
  const browser = await chromium.launch({ headless: false, slowMo: 300 });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

  const filePath = 'file://' + path.resolve(__dirname, 'index.html');
  await page.goto(filePath);

  console.log('✅ Page loaded - watch the browser!');
  await page.waitForTimeout(1000);

  // Fill in the form step by step
  console.log('✏️ Filling in First Name...');
  await page.fill('#firstName', 'John');
  await page.waitForTimeout(500);

  console.log('✏️ Filling in Last Name...');
  await page.fill('#lastName', 'Doe');
  await page.waitForTimeout(500);

  console.log('✏️ Filling in Email...');
  await page.fill('#email', 'john.doe@example.com');
  await page.waitForTimeout(500);

  console.log('✏️ Filling in Phone...');
  await page.fill('#phone', '+1 (555) 123-4567');
  await page.waitForTimeout(500);

  console.log('✏️ Filling in Password...');
  await page.fill('#password', 'SecurePass123!');
  await page.waitForTimeout(500);

  console.log('✏️ Filling in Confirm Password...');
  await page.fill('#confirmPassword', 'SecurePass123!');
  await page.waitForTimeout(500);

  console.log('🔘 Clicking Register...');
  await page.click('#registerBtn');
  await page.waitForTimeout(1000);

  // Check success
  const successMsg = await page.$('#successMessage');
  const visible = await successMsg.evaluate(el => el.classList.contains('visible'));
  if (visible) {
    console.log('✅ Registration Successful! 🎉');
  }

  // Keep browser open for 5 seconds so you can see it
  console.log('⏳ Browser will close in 5 seconds...');
  await page.waitForTimeout(5000);

  await browser.close();
  console.log('🏁 Done!');
})().catch(err => {
  console.error('❌ Error:', err.message);
  process.exit(1);
});
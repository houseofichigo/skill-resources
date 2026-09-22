const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium } = require("playwright");

async function main() {
  const root = path.resolve(__dirname, "..");
  const source = path.join(root, "infographic", "which-ai-model.html");
  const output = path.join(root, "infographic", "which-ai-model.png");
  const browser = await chromium.launch({ headless: true });

  try {
    const page = await browser.newPage({
      viewport: { width: 1600, height: 1000 },
      deviceScaleFactor: 2,
    });
    await page.goto(pathToFileURL(source).href, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: output, fullPage: true });
    console.log(`Wrote ${output}`);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

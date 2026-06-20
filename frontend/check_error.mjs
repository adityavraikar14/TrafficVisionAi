import { chromium } from "playwright";
import path from "path";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.on("console", (msg) => console.log("[console]", msg.type(), msg.text()));
page.on("pageerror", (err) => console.log("[pageerror]", err.message));

await page.goto("http://localhost:5173/video-analysis", { waitUntil: "networkidle" });
const filePath = path.resolve("../sample_images/Video-418.mp4");
await page.setInputFiles('input[type="file"]', filePath);
await page.waitForTimeout(600);

await page.click('button:has-text("Run Video Analysis")');
await page.waitForTimeout(2000);
await page.screenshot({ path: "/tmp/shots/error_display_check.png", fullPage: true });
console.log("done");
await browser.close();

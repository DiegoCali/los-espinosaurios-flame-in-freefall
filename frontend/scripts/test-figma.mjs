import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = '/home/ponche/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome';

async function capture(url, outPath, waitMs = 25000, width = 1440, height = 900) {
  console.log(`Starting capture for ${url}...`);
  const port = 9222 + Math.floor(Math.random() * 500);
  const chrome = spawn(CHROME_PATH, [
    '--headless=new',
    '--no-sandbox',
    '--use-gl=angle',
    '--use-angle=swiftshader',
    '--enable-unsafe-swiftshader',
    '--disable-gpu-sandbox',
    `--remote-debugging-port=${port}`,
    '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    `--window-size=${width},${height}`,
    `--user-data-dir=/tmp/figma-profile-${port}`,
    'about:blank'
  ]);

  try {
    // Wait for CDP to be available
    let versionData = null;
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 300));
      try {
        const res = await fetch(`http://127.0.0.1:${port}/json/version`);
        if (res.ok) {
          versionData = await res.json();
          break;
        }
      } catch (e) {}
    }
    if (!versionData) throw new Error('Could not connect to Chrome CDP');

    // Create a new target / page
    const newTargetRes = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
    const target = await newTargetRes.json();
    console.log('Connected to target:', target.id);

    const ws = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.onopen = resolve;
      ws.onerror = reject;
    });

    let id = 1;
    const callbacks = new Map();
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && callbacks.has(msg.id)) {
        callbacks.get(msg.id)(msg);
        callbacks.delete(msg.id);
      }
      if (msg.method === 'Runtime.consoleAPICalled') {
        const text = msg.params.args.map(a => a.value || JSON.stringify(a)).join(' ');
        console.log('[Browser Console]:', text.slice(0, 200));
      }
    };

    function send(method, params = {}) {
      return new Promise((resolve) => {
        const msgId = id++;
        callbacks.set(msgId, resolve);
        ws.send(JSON.stringify({ id: msgId, method, params }));
      });
    }

    await send('Runtime.enable');
    await send('Page.enable');
    await send('DOM.enable');

    console.log(`Waiting ${waitMs}ms for Figma WASM/WebGL canvas to load...`);
    await new Promise(r => setTimeout(r, waitMs));

    // Capture screenshot
    const res = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    if (res.result && res.result.data) {
      const buffer = Buffer.from(res.result.data, 'base64');
      writeFileSync(outPath, buffer);
      console.log(`Saved screenshot to ${outPath} (${buffer.length} bytes)`);
    } else {
      console.error('Failed to capture screenshot:', res);
    }

    ws.close();
  } finally {
    chrome.kill();
  }
}

async function main() {
  const url = process.argv[2] || 'https://www.figma.com/design/Uku1QlSTwB6PVpm5ikM5c8/Spinosaurios-Research-Hub?node-id=326-27';
  const out = process.argv[3] || '/tmp/figma-rendered.png';
  await capture(url, out, 25000);
}

main().catch(console.error);

import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = '/home/ponche/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome';

export async function captureFigmaFrame(nodeId, outPrefix, options = {}) {
  const url = `https://www.figma.com/design/Uku1QlSTwB6PVpm5ikM5c8/Spinosaurios-Research-Hub?node-id=${encodeURIComponent(nodeId)}`;
  console.log(`Starting capture for node ${nodeId} at ${url}...`);
  const port = 9222 + Math.floor(Math.random() * 500);
  const width = options.width || 1920;
  const height = options.height || 1080;
  
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

    console.log('Waiting 22s for initial load...');
    await new Promise(r => setTimeout(r, 22000));

    // Send Shift+2 to zoom to selection
    console.log('Sending Shift+2 (Zoom to selection)...');
    await send('Input.dispatchKeyEvent', {
      type: 'keyDown',
      modifiers: 8, // Shift
      key: '2',
      code: 'Digit2',
      windowsVirtualKeyCode: 50,
      nativeVirtualKeyCode: 50,
    });
    await send('Input.dispatchKeyEvent', {
      type: 'keyUp',
      modifiers: 0,
      key: '2',
      code: 'Digit2',
      windowsVirtualKeyCode: 50,
      nativeVirtualKeyCode: 50,
    });

    await new Promise(r => setTimeout(r, 3000));

    // Also close the banner if present by pressing Escape
    await send('Input.dispatchKeyEvent', {
      type: 'keyDown',
      key: 'Escape',
      code: 'Escape',
      windowsVirtualKeyCode: 27,
      nativeVirtualKeyCode: 27,
    });
    await send('Input.dispatchKeyEvent', {
      type: 'keyUp',
      key: 'Escape',
      code: 'Escape',
      windowsVirtualKeyCode: 27,
      nativeVirtualKeyCode: 27,
    });

    await new Promise(r => setTimeout(r, 1000));

    // Screenshot 1: Overview after zoom to selection
    let res = await send('Page.captureScreenshot', { format: 'png' });
    if (res.result && res.result.data) {
      writeFileSync(`${outPrefix}-zoomed.png`, Buffer.from(res.result.data, 'base64'));
      console.log(`Saved ${outPrefix}-zoomed.png`);
    }

    // Now let's pan down using PageDown or Down Arrow or scroll
    // In Figma canvas, space + drag or mouse wheel or PageDown pans
    for (let scrollStep = 1; scrollStep <= 5; scrollStep++) {
      console.log(`Scrolling step ${scrollStep}...`);
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: 700,
      });
      await new Promise(r => setTimeout(r, 1500));
      res = await send('Page.captureScreenshot', { format: 'png' });
      if (res.result && res.result.data) {
        writeFileSync(`${outPrefix}-part-${scrollStep}.png`, Buffer.from(res.result.data, 'base64'));
        console.log(`Saved ${outPrefix}-part-${scrollStep}.png`);
      }
    }

    ws.close();
  } finally {
    chrome.kill();
  }
}

async function main() {
  const target = process.argv[2] || '326-27';
  const prefix = process.argv[3] || '/tmp/figma-acme-desktop';
  await captureFigmaFrame(target, prefix, { width: 1920, height: 1080 });
}

main().catch(console.error);

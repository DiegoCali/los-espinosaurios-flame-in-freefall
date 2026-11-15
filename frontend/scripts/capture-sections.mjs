import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = '/home/ponche/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome';

async function captureDetailed(nodeId, outPrefix, options = {}) {
  const url = `https://www.figma.com/design/Uku1QlSTwB6PVpm5ikM5c8/Spinosaurios-Research-Hub?node-id=${encodeURIComponent(nodeId)}`;
  const port = 9444 + Math.floor(Math.random() * 400);
  const width = options.width || 2560;
  const height = options.height || 1440;

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
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 300));
      try {
        const res = await fetch(`http://127.0.0.1:${port}/json/version`);
        if (res.ok) break;
      } catch (e) {}
    }

    const newTargetRes = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' });
    const target = await newTargetRes.json();
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

    console.log('Waiting 22s for load...');
    await new Promise(r => setTimeout(r, 22000));

    // Dismiss bottom banner
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });

    // Focus on canvas
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: width / 2, y: height / 2, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: width / 2, y: height / 2, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 500));

    // Shift + 0 to set 100% zoom
    console.log('Sending Shift+0 (100% zoom)...');
    await send('Input.dispatchKeyEvent', { type: 'rawKeyDown', modifiers: 8, key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16 });
    await send('Input.dispatchKeyEvent', { type: 'keyDown', modifiers: 8, key: ')', text: '0', code: 'Digit0', windowsVirtualKeyCode: 48 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 8, key: ')', code: 'Digit0', windowsVirtualKeyCode: 48 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', modifiers: 0, key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16 });
    await new Promise(r => setTimeout(r, 1500));

    // Zoom out slightly (50%) with Ctrl + '-' or Ctrl+Wheel so entire 1440 width fits in 2560
    for (let i = 0; i < 4; i++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: 120,
        modifiers: 2 // Ctrl
      });
    }
    await new Promise(r => setTimeout(r, 1500));

    // Pan up to the very top (Page Up multiple times or wheel up)
    console.log('Panning to top of frame...');
    for (let i = 0; i < 15; i++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: -800,
        modifiers: 0
      });
    }
    await new Promise(r => setTimeout(r, 2000));

    // Now take 8 sequential slices down the frame
    for (let step = 1; step <= 8; step++) {
      const res = await send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(`${outPrefix}-slice-${step}.png`, Buffer.from(res.result.data, 'base64'));
      console.log(`Saved ${outPrefix}-slice-${step}.png`);

      // Scroll down
      for (let p = 0; p < 2; p++) {
        await send('Input.dispatchMouseEvent', {
          type: 'mouseWheel',
          x: width / 2,
          y: height / 2,
          deltaX: 0,
          deltaY: 600,
          modifiers: 0
        });
      }
      await new Promise(r => setTimeout(r, 1200));
    }

    ws.close();
  } finally {
    chrome.kill();
  }
}

async function main() {
  const node = process.argv[2] || '326-27';
  const prefix = process.argv[3] || '/tmp/acme-desktop';
  await captureDetailed(node, prefix);
}

main().catch(console.error);

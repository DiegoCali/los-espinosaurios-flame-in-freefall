import { spawn } from 'child_process';
import { writeFileSync } from 'fs';

const CHROME_PATH = '/home/ponche/.cache/puppeteer/chrome/linux-157.0.8103.50/chrome-linux64/chrome';

async function captureClean(nodeId, outPrefix) {
  const url = `https://www.figma.com/design/Uku1QlSTwB6PVpm5ikM5c8/Spinosaurios-Research-Hub?node-id=${encodeURIComponent(nodeId)}`;
  const port = 9555;
  const width = 1920;
  const height = 1200;

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
    `--user-data-dir=/tmp/figma-profile-clean`,
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

    // Dismiss bottom banner with Escape
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });

    // Focus canvas
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: width / 2, y: height / 2, button: 'left', clickCount: 1 });
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: width / 2, y: height / 2, button: 'left', clickCount: 1 });
    await new Promise(r => setTimeout(r, 500));

    // Zoom in 9 ticks with Ctrl + wheel
    console.log('Zooming in to ~35-40%...');
    for (let i = 0; i < 9; i++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: -120,
        modifiers: 2 // Ctrl
      });
    }
    await new Promise(r => setTimeout(r, 2000));

    // Pan up to top: deltaY < 0 pans up (brings top down into view)
    console.log('Panning up to top...');
    for (let i = 0; i < 8; i++) {
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: -400,
        modifiers: 0
      });
    }
    await new Promise(r => setTimeout(r, 1500));

    // Capture initial top view
    let res = await send('Page.captureScreenshot', { format: 'png' });
    writeFileSync(`${outPrefix}-01-top.png`, Buffer.from(res.result.data, 'base64'));
    console.log(`Saved ${outPrefix}-01-top.png`);

    // Now pan down sequentially
    for (let step = 2; step <= 8; step++) {
      console.log(`Panning to section ${step}...`);
      await send('Input.dispatchMouseEvent', {
        type: 'mouseWheel',
        x: width / 2,
        y: height / 2,
        deltaX: 0,
        deltaY: 500,
        modifiers: 0
      });
      await new Promise(r => setTimeout(r, 1200));
      res = await send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(`${outPrefix}-0${step}.png`, Buffer.from(res.result.data, 'base64'));
      console.log(`Saved ${outPrefix}-0${step}.png`);
    }

    ws.close();
  } finally {
    chrome.kill();
  }
}

captureClean(process.argv[2] || '326-27', process.argv[3] || '/tmp/acme-view').catch(console.error);

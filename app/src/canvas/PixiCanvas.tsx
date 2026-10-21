import { Application } from 'pixi.js';
import { useEffect, useRef, useState } from 'react';

export function PixiCanvas() {
  const host = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    const element = host.current;
    if (!element) return;
    const app = new Application();
    let disposed = false;
    let initialized = false;
    void (async () => {
      try {
        await app.init({
          resizeTo: element,
          backgroundAlpha: 0,
          antialias: true,
          preference: 'webgl',
        });
        initialized = true;
        if (disposed) {
          app.destroy(true);
          return;
        }
        app.canvas.setAttribute('aria-label', '빈 애니메이션 캔버스');
        app.canvas.setAttribute('role', 'img');
        element.appendChild(app.canvas);
        setStatus('ready');
      } catch {
        if (initialized) app.destroy(true);
        if (!disposed) setStatus('error');
      }
    })();
    return () => {
      disposed = true;
      if (initialized) app.destroy(true);
    };
  }, []);

  return (
    <div
      className="canvas-host"
      ref={host}
      data-testid="pixi-stage"
      data-status={status}
    >
      {status === 'error' && (
        <p role="alert">
          캔버스를 시작할 수 없습니다. WebGL을 지원하는 브라우저에서 다시 열어
          주세요.
        </p>
      )}
    </div>
  );
}

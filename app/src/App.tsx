import { PixiCanvas } from './canvas/PixiCanvas';
import { FPS, FRAME_LABELS } from './timeline';

export function App() {
  return (
    <main className="workspace">
      <header className="toolbar">
        <h1>Sikk2d</h1>
        <span>새 프로젝트</span>
        <span className="badge">초기 환경</span>
      </header>
      <aside className="layers" aria-label="레이어">
        <h2>레이어</h2>
        <p>아직 레이어가 없습니다.</p>
      </aside>
      <section className="viewport" aria-label="작업 영역">
        <PixiCanvas />
        <div className="canvas-caption">빈 캔버스</div>
      </section>
      <aside className="inspector" aria-label="속성">
        <h2>속성</h2>
        <p>선택한 항목이 없습니다.</p>
      </aside>
      <section className="timeline" aria-label="타임라인">
        <div className="timeline-heading">
          <h2>타임라인</h2>
          <span>{FPS} FPS · 24 프레임</span>
        </div>
        <div className="ruler" aria-label="프레임 눈금">
          {FRAME_LABELS.map((frame) => (
            <span key={frame}>{frame}</span>
          ))}
        </div>
        <p>키프레임이 없습니다.</p>
      </section>
      <footer>
        캔버스와 타임라인 준비 완료 · 편집 기능은 다음 단계에서 제공됩니다.
      </footer>
    </main>
  );
}

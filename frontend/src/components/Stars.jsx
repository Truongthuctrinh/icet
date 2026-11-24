import { useState } from "react";

/** Hiển thị sao (điểm thập phân được làm tròn tới nửa sao). */
export function StarDisplay({ value, size = "text-base" }) {
  const rounded = Math.round(value * 2) / 2;
  return (
    <span className={`inline-flex tracking-[0.05em] ${size}`} aria-label={`${value.toFixed(1)} trên 5 sao`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= rounded ? "text-marigold" : i - 0.5 === rounded ? "text-marigold/60" : "text-mist"}>
          ★
        </span>
      ))}
    </span>
  );
}

/** Chọn số sao (bàn phím: Tab tới từng sao, Enter/Space để chọn). */
export function StarInput({ value, onChange }) {
  const [hover, setHover] = useState(0);
  const shown = hover || value;
  const labels = ["", "Tệ", "Chưa hay", "Tạm được", "Hay", "Rất hay"];
  return (
    <div className="flex items-center gap-3">
      <div className="flex" role="radiogroup" aria-label="Số sao" onMouseLeave={() => setHover(0)}>
        {[1, 2, 3, 4, 5].map((i) => (
          <button
            key={i}
            type="button"
            role="radio"
            aria-checked={value === i}
            aria-label={`${i} sao`}
            onMouseEnter={() => setHover(i)}
            onClick={() => onChange(i)}
            className={`px-0.5 text-2xl leading-none transition-colors ${i <= shown ? "text-marigold" : "text-mist"}`}
          >
            ★
          </button>
        ))}
      </div>
      <span className="text-sm text-ink-soft">{labels[shown]}</span>
    </div>
  );
}

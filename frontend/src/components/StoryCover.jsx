/** Bìa chữ tự sinh khi truyện chưa có ảnh: màu chọn ổn định theo tên truyện. */
const PALETTES = [
  { bg: "#2f2a5a", fg: "#f4efe1", accent: "#f2b84b" },
  { bg: "#1f4a45", fg: "#eef3ea", accent: "#e9c46a" },
  { bg: "#6b2f3a", fg: "#f8ece6", accent: "#f2b84b" },
  { bg: "#273b5c", fg: "#e8eef7", accent: "#9ec5ff" },
  { bg: "#4a3b2a", fg: "#f5ecdc", accent: "#e9a65c" },
  { bg: "#3d2c4f", fg: "#f1e9f7", accent: "#d9a7f2" },
];

function hash(text) {
  let h = 0;
  for (const ch of text) h = (h * 31 + ch.codePointAt(0)) >>> 0;
  return h;
}

const SIZES = {
  sm: "w-14 h-20 text-[0.55rem] p-1.5",
  md: "w-24 h-36 text-[0.8rem] p-2.5",
  lg: "w-36 h-52 text-[1.05rem] p-3.5 sm:w-44 sm:h-64 sm:text-[1.2rem]",
};

const IMAGE_SIZES = {
  sm: "w-14 h-20",
  md: "w-24 h-36",
  lg: "w-36 h-52 sm:w-44 sm:h-64",
};

/** previewUrl: ảnh đang chọn ở form (chưa tải lên). Không có ảnh -> bìa chữ tự sinh. */
export default function StoryCover({ story, size = "md", className = "", previewUrl }) {
  const image = previewUrl ?? story.cover_url;
  if (image) {
    return (
      <img
        src={image}
        alt=""
        aria-hidden="true"
        loading="lazy"
        className={`shrink-0 rounded-md object-cover shadow-sm ${IMAGE_SIZES[size]} ${className}`}
      />
    );
  }
  const p = PALETTES[hash(story.title || "") % PALETTES.length];
  return (
    <div
      aria-hidden="true"
      className={`relative flex shrink-0 flex-col justify-between overflow-hidden rounded-md shadow-sm ${SIZES[size]} ${className}`}
      style={{ backgroundColor: p.bg, color: p.fg }}
    >
      <span style={{ color: p.accent }} className="leading-none">
        ✦
      </span>
      <span className="font-serif leading-[1.15] [overflow-wrap:anywhere]">
        {size === "sm" ? (story.title || "").slice(0, 40) : story.title || "Tên truyện"}
      </span>
      {size !== "sm" && (
        <span className="truncate text-[0.7em] opacity-70">{story.author?.display_name}</span>
      )}
    </div>
  );
}

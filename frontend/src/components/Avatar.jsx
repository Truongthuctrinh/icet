const SIZES = {
  xs: "h-6 w-6 text-[0.7rem]",
  sm: "h-8 w-8 text-sm",
  lg: "h-16 w-16 text-2xl",
  xl: "h-24 w-24 text-4xl",
};

/** Ảnh đại diện; chưa có ảnh thì hiện chữ cái đầu của tên. */
export default function Avatar({ user, size = "sm", src, className = "" }) {
  const image = src ?? user?.avatar_url;
  const base = `shrink-0 rounded-full ${SIZES[size]} ${className}`;
  if (image) {
    return <img src={image} alt="" aria-hidden="true" loading="lazy" className={`${base} object-cover`} />;
  }
  return (
    <span aria-hidden="true" className={`${base} flex items-center justify-center bg-dusk font-serif text-white`}>
      {(user?.display_name || "?").trim().charAt(0).toUpperCase()}
    </span>
  );
}

import { Button } from "../components/ui";

export default function NotFoundPage() {
  return (
    <div className="mx-auto max-w-xl px-5 py-24 text-center">
      <p className="font-serif text-6xl text-marigold" aria-hidden="true">✦</p>
      <h1 className="mt-4 font-serif text-3xl">Trang này chưa được viết ra</h1>
      <p className="mt-3 text-ink-soft">Đường dẫn không tồn tại hoặc đã bị gỡ.</p>
      <div className="mt-8">
        <Button to="/">Về trang chủ</Button>
      </div>
    </div>
  );
}

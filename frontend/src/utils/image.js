// Kiểm tra sơ bộ ở trình duyệt để báo lỗi ngay; backend vẫn kiểm tra lại kỹ (không tin trình duyệt)
export const IMAGE_ACCEPT = "image/jpeg,image/png,image/webp";
export const MAX_IMAGE_MB = 2;

export function checkImageFile(file) {
  if (!file) return "Chưa chọn ảnh";
  if (!IMAGE_ACCEPT.split(",").includes(file.type)) return "Chỉ nhận ảnh JPG, PNG hoặc WebP";
  if (file.size > MAX_IMAGE_MB * 1024 * 1024) return `Ảnh tối đa ${MAX_IMAGE_MB} MB`;
  return "";
}

"""Tạo dữ liệu mẫu để demo / chấm bài: 1 admin, 3 tác giả, 3 truyện, 1 vụ chép nguyên văn + 1 vụ viết lại.

Chạy (chỉ chạy được khi DB còn trống người dùng, để không đụng dữ liệu thật):
    python -m app.scripts.seed_demo                       # chạy thường
    docker compose exec api python -m app.scripts.seed_demo   # chạy trong Docker

Mật khẩu mọi tài khoản mẫu: matkhau123  (admin: SEED_ADMIN_PASSWORD trong .env, mặc định admin12345)
"""
import asyncio
import os
import time

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Genre, User
from app.schemas.chapter import ChapterCreate
from app.schemas.story import StoryCreate, StoryUpdate
from app.schemas.user import UserCreate
from app.services.auth_service import register_user
from app.services.chapter_service import create_chapter
from app.services.plagiarism_service import run_check_in_background
from app.services.story_service import create_story, update_story

PASSWORD = "matkhau123"

HO_KY_UC_1 = [
    "Mười năm sau trận lũ, lần đầu tiên Lam quay về thị trấn cũ. Mặt hồ phẳng lặng đến mức cô có thể nhìn thấy mây trôi qua mái ngói của trường tiểu học.",
    "Người lái đò bảo cô đừng lặn vào buổi chiều. Ông nói khi mặt trời chếch về phía núi, nước hồ đổi màu, và những ai ở dưới đó bắt đầu thức dậy.",
    "Lam cười, buộc lại dây kính lặn. Cô không tin chuyện ma quỷ. Cô chỉ muốn tìm lại chiếc hộp thiếc mẹ đã chôn dưới gốc cây khế trước nhà.",
    "Nước lạnh hơn cô tưởng. Ở độ sâu năm mét, ánh sáng mờ dần thành màu xanh ngọc, rồi xanh lục, rồi một thứ màu không có tên.",
    "Và rồi cô nghe thấy nó: tiếng chuông trường, ba hồi dài, đúng như những buổi sáng thứ hai năm cô mười tuổi khi cả lớp xếp hàng.",
]
HO_KY_UC_2 = [
    "Cô ngoi lên, thở dốc. Trên bờ, người lái đò vẫn ngồi im, điếu thuốc cháy dở giữa hai ngón tay, như thể ông đã biết trước chuyện này.",
    "Ông không hỏi cô nghe thấy gì. Ông chỉ chỉ tay về phía rặng tre, nơi ngày xưa là con đường dẫn lên chợ, rồi bảo cô về nhà nghỉ đi.",
    "Đêm đó Lam không ngủ được. Cô mở cuốn sổ cũ của mẹ, lật đến trang có vẽ sơ đồ khu vườn, và thấy một dấu nhân nhỏ không nằm dưới gốc khế.",
]
GIO_MUA = [
    "Gió mùa đông bắc tràn về sớm hơn mọi năm. Trên con đường đất đỏ dẫn ra bến xe, Tuấn kéo chiếc vali cũ kỹ, bánh xe kêu lọc cọc.",
    "Bến xe vắng tanh. Chỉ có một bà cụ bán bánh mì ngồi co ro bên bếp than hồng, khói bay lên hòa vào màn sương dày đặc.",
    "Anh mua hai ổ bánh mì, ăn một ổ, ổ còn lại bọc kỹ trong tờ báo cũ. Mẹ anh vẫn dặn đi đường xa thì phải giữ một miếng phòng thân.",
    "Chuyến xe sáu giờ đến muộn bốn mươi phút. Tuấn chọn ghế cuối, áp trán vào cửa kính lạnh buốt, nhìn ngôi làng nhỏ dần rồi biến mất sau đồi.",
]
# Tài khoản "daovan": 1 đoạn chép nguyên văn + 3 đoạn viết lại từ "Hồ ký ức"
BAN_SAO = [
    GIO_MUA[0],
    "Đã mười năm kể từ trận lụt, Lam mới trở lại phố huyện cũ lần đầu. Hồ nước yên đến nỗi nàng thấy được mây lướt ngang mái ngói trường tiểu học.",
    "Ông chèo thuyền dặn nàng chớ có xuống nước lúc hoàng hôn. Theo ông, lúc nắng nghiêng về phía đồi, hồ chuyển sắc và những kẻ dưới ấy tỉnh dậy.",
    "Lam mỉm cười, thắt lại kính lặn. Nàng chẳng tin ma quỷ gì cả. Nàng chỉ mong tìm được cái rương thiếc má từng vùi dưới gốc khế trước nhà.",
    HO_KY_UC_1[4],
]


def _user(db, username, display_name, password=PASSWORD, role="user") -> User:
    user = register_user(
        db, UserCreate(username=username, email=f"{username}@icet.vn", password=password, display_name=display_name)
    )
    if role != "user":
        user.role = role
        db.commit()
    return user


def _story(db, author, title, description, genre_slugs, chapters):
    genre_ids = list(db.scalars(select(Genre.id).where(Genre.slug.in_(genre_slugs))))
    story = create_story(db, author, StoryCreate(title=title, description=description, genre_ids=genre_ids))
    update_story(db, story, StoryUpdate(is_published=True))
    ids = []
    for i, paragraphs in enumerate(chapters, start=1):
        chapter = create_chapter(
            db, story, ChapterCreate(title=f"Chương {i}", content="\n\n".join(paragraphs), is_published=True)
        )
        ids.append(chapter.id)
        time.sleep(1.1)  # thời điểm đăng khác nhau -> hệ thống biết ai viết trước
    return ids


async def _enqueue_reindex() -> bool:
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL), retry=1)
        await pool.enqueue_job("reindex_job")
        await pool.aclose()
        return True
    except Exception:
        return False


def main() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(func.count(User.id))):
            print("Database đã có người dùng, bỏ qua để không ghi đè dữ liệu thật.")
            return
        _user(db, "admin", "Quản trị viên", os.environ.get("SEED_ADMIN_PASSWORD", "admin12345"), role="admin")
        lam = _user(db, "lamthu", "Lam Thư")
        tuan = _user(db, "tuanvu", "Tuấn Vũ")
        dv = _user(db, "daovan", "Người Viết Lại")

        chapter_ids = []
        chapter_ids += _story(db, lam, "Hồ ký ức", "Mười năm sau trận lũ, Lam quay về thị trấn cũ để tìm chiếc hộp mẹ chôn.",
                              ["huyen-huyen", "doi-thuong"], [HO_KY_UC_1, HO_KY_UC_2])
        chapter_ids += _story(db, tuan, "Gió mùa đông bắc", "Tuấn rời làng trong một buổi sáng sương mù.",
                              ["doi-thuong"], [GIO_MUA])
        chapter_ids += _story(db, dv, "Bản sao", "Truyện mẫu dùng để demo phát hiện đạo văn.",
                              ["huyen-huyen"], [BAN_SAO])
    finally:
        db.close()

    if asyncio.run(_enqueue_reindex()):
        print("Đã giao cho worker kiểm tra đạo văn (cả nguyên văn lẫn viết lại).")
    else:
        for chapter_id in chapter_ids:  # không có worker -> chỉ so nguyên văn
            run_check_in_background(chapter_id)
        print("Không thấy worker: đã kiểm tra nguyên văn. Bật worker rồi bấm 'Quét lại' ở trang Đạo văn để so cả ý.")

    print("\nTài khoản mẫu (mật khẩu matkhau123): lamthu, tuanvu, daovan")
    print("Admin: admin /", os.environ.get("SEED_ADMIN_PASSWORD", "admin12345"))


if __name__ == "__main__":
    main()

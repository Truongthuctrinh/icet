import { Link } from "react-router";
import { timeAgo } from "../utils/format";
import StoryCover from "./StoryCover";
import { StarDisplay } from "./Stars";
import { StatusBadge } from "./ui";

/** 1 dòng truyện trong danh sách: bìa + tên + tác giả + thể loại + đánh giá. */
export default function StoryListItem({ story, showAuthor = true }) {
  return (
    <li>
      <Link to={`/truyen/${story.id}`} className="group flex gap-5 py-6">
        <StoryCover story={story} size="md" className="hidden sm:flex" />
        <StoryCover story={story} size="sm" className="sm:hidden" />
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline justify-between gap-4">
            <h3 className="font-serif text-xl text-ink transition-colors group-hover:text-dusk sm:text-[1.375rem]">
              {story.title}
            </h3>
            <span className="hidden shrink-0 text-sm text-ink-soft sm:inline">{timeAgo(story.updated_at)}</span>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm text-ink-soft">
            {showAuthor && <span>{story.author.display_name}</span>}
            <StatusBadge status={story.status} />
            {story.rating_count > 0 && (
              <span className="inline-flex items-center gap-1.5">
                <StarDisplay value={story.rating_avg} size="text-sm" />
                <span className="tabular-nums">{story.rating_avg.toFixed(1)}</span>
              </span>
            )}
            {story.follower_count > 0 && <span>{story.follower_count} người theo dõi</span>}
          </div>
          {story.genres.length > 0 && (
            <p className="mt-2 text-[0.8125rem] text-dusk">{story.genres.map((g) => g.name).join(", ")}</p>
          )}
          <p className="mt-2 line-clamp-2 max-w-2xl leading-relaxed text-ink/80">
            {story.description || "Tác giả chưa viết giới thiệu cho truyện này."}
          </p>
        </div>
      </Link>
    </li>
  );
}

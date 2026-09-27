// 当前时间范围无文章时提示检查采集快照或调整筛选条件。
import { SearchX } from 'lucide-react'

/** 展示无资讯或无搜索结果的提示。 */
export function EmptyState() {
  return (
    <div className="card p-12 text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 mb-4">
        <SearchX className="w-8 h-8 text-slate-400" />
      </div>
      <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
        当前没有相关资讯
      </h3>
      <p className="text-slate-500 dark:text-slate-400">
        请先运行采集命令，或调整时间范围、筛选条件和搜索词
      </p>
    </div>
  )
}

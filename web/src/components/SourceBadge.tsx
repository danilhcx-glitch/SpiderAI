// 根据来源类型选择资讯卡片上的颜色标签。
import { SITE_COLORS, DEFAULT_BADGE_COLOR } from '../utils/constants'

interface SourceBadgeProps {
  siteId: string
  siteName: string
}

/** 为 RSS、公众号和网页来源显示对应颜色。 */
export function SourceBadge({ siteId, siteName }: SourceBadgeProps) {
  const colorClass = SITE_COLORS[siteId] || DEFAULT_BADGE_COLOR
  
  return (
    <span className={`badge ${colorClass}`}>
      {siteName}
    </span>
  )
}

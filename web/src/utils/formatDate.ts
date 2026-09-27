// 资讯时间统一使用中文本地格式，无法解析时显示明确的未知状态。
import { formatDistanceToNow, format, parseISO, isValid } from 'date-fns'
import { zhCN } from 'date-fns/locale'

/** 把 ISO 时间转换为相对时间。 */
export function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return '未知时间'
  
  try {
    const date = parseISO(dateString)
    if (!isValid(date)) return '未知时间'
    
    return formatDistanceToNow(date, { 
      addSuffix: true, 
      locale: zhCN 
    })
  } catch {
    return '未知时间'
  }
}

/** 把 ISO 时间转换为日期和分钟。 */
export function formatDateTime(dateString: string | null): string {
  if (!dateString) return '未知时间'
  
  try {
    const date = parseISO(dateString)
    if (!isValid(date)) return '未知时间'
    
    return format(date, 'yyyy-MM-dd HH:mm', { locale: zhCN })
  } catch {
    return '未知时间'
  }
}

/** 只提取 ISO 时间中的本地时分。 */
export function formatTime(dateString: string | null): string {
  if (!dateString) return ''
  
  try {
    const date = parseISO(dateString)
    if (!isValid(date)) return ''
    
    return format(date, 'HH:mm', { locale: zhCN })
  } catch {
    return ''
  }
}

// 阅读历史保存在当前浏览器，兼容参考前端旧版的时间戳结构。
import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'ai-news-visited-links'
const MAX_LINKS = 1000

export interface VisitedLinkInfo {
  timestamp: number
  title: string
}

/** 读取历史记录，并迁移仅保存时间戳的旧数据。 */
function getStoredLinks(): Record<string, VisitedLinkInfo> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed.links) {
        const firstValue = Object.values(parsed.links)[0]
        if (typeof firstValue === 'number') {
          const migrated: Record<string, VisitedLinkInfo> = {}
          for (const [url, timestamp] of Object.entries(parsed.links)) {
            migrated[url] = { timestamp: timestamp as number, title: '' }
          }
          return migrated
        }
        return parsed.links
      }
    }
  } catch {
    console.warn('Failed to parse visited links from localStorage')
  }
  return {}
}

/** 限制本地记录数量并保存最新的阅读历史。 */
function saveLinks(links: Record<string, VisitedLinkInfo>) {
  try {
    const entries = Object.entries(links)
    if (entries.length > MAX_LINKS) {
      const sorted = entries.sort((a, b) => a[1].timestamp - b[1].timestamp)
      const trimmed = sorted.slice(entries.length - MAX_LINKS)
      links = Object.fromEntries(trimmed)
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ links }))
  } catch {
    console.warn('Failed to save visited links to localStorage')
  }
}

/** 向资讯卡片和历史弹窗提供已读状态。 */
export function useVisitedLinks() {
  const [visitedLinks, setVisitedLinks] = useState<Record<string, VisitedLinkInfo>>(() => getStoredLinks())

  useEffect(() => {
    saveLinks(visitedLinks)
  }, [visitedLinks])

  const markAsVisited = useCallback((url: string, title?: string) => {
    setVisitedLinks(prev => ({
      ...prev,
      [url]: { timestamp: Date.now(), title: title || '' }
    }))
  }, [])

  const isVisited = useCallback((url: string) => {
    return url in visitedLinks
  }, [visitedLinks])

  const clearAll = useCallback(() => {
    setVisitedLinks({})
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  return {
    visitedLinks,
    markAsVisited,
    isVisited,
    clearAll,
    visitedCount: Object.keys(visitedLinks).length
  }
}

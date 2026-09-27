// 收藏以 SQLite 为准；首次打开新版页面时把旧浏览器收藏迁入数据库。
import { useState, useEffect, useCallback, useRef } from 'react'

const STORAGE_KEY = 'ai-news-favorites'
const MIGRATION_KEY = 'ai-news-favorites-migrated'
const MAX_FAVORITES = 500

export interface FavoriteInfo {
  timestamp: number
  title: string
}

type Favorites = Record<string, FavoriteInfo>

/** 读取至多 500 条旧浏览器收藏，供一次性迁移使用。 */
function getStoredFavorites(): Favorites {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return {}
    const parsed = JSON.parse(stored)
    if (!parsed?.favorites || typeof parsed.favorites !== 'object' || Array.isArray(parsed.favorites)) return {}
    return Object.fromEntries(Object.entries(parsed.favorites).slice(-MAX_FAVORITES)) as Favorites
  } catch {
    console.warn('无法读取旧浏览器收藏')
    return {}
  }
}

/** 将旧收藏导入后端；成功后才标记迁移完成，避免失败时丢失原记录。 */
async function loadFavorites(): Promise<Favorites> {
  let migrated = false
  try {
    migrated = localStorage.getItem(MIGRATION_KEY) === '1'
  } catch {
    // 浏览器禁用本地存储时，后端仍可处理新的收藏。
  }
  const legacy = migrated ? {} : getStoredFavorites()
  const response = await fetch('/api/favorites/import', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ favorites: legacy }),
  })
  if (!response.ok) throw new Error('收藏迁移失败')
  const data = await response.json() as { favorites: Favorites }
  // 标记成功后旧数据不再参与同步，避免已取消的收藏被下次刷新重新导入。
  try {
    localStorage.setItem(MIGRATION_KEY, '1')
    localStorage.removeItem(STORAGE_KEY)
  } catch {
    console.warn('无法清理旧浏览器收藏缓存')
  }
  return data.favorites
}

/** 通过本地接口管理收藏，按操作顺序写入 SQLite。 */
export function useFavorites() {
  const [favorites, setFavorites] = useState<Favorites>(() => getStoredFavorites())
  const [error, setError] = useState<string | null>(null)
  const current = useRef(favorites)
  const initialized = useRef<Promise<void>>(Promise.resolve())
  const pending = useRef<Promise<void>>(Promise.resolve())
  const started = useRef(false)

  /** 同时更新渲染状态和异步操作读取的最新收藏。 */
  const update = useCallback((next: Favorites) => {
    current.current = next
    setFavorites(next)
  }, [])

  useEffect(() => {
    // React 开发模式会重复执行 effect，迁移只需启动一次。
    if (started.current) return
    started.current = true
    const task = loadFavorites().then(next => {
      update(next)
      setError(null)
    }).catch(reason => {
      setError('收藏迁移失败，请刷新页面重试；旧浏览器收藏仍在本地。')
      throw reason
    })
    initialized.current = task
    void task.catch(() => undefined)
  }, [update])

  /** 排队执行写操作，避免快速点击造成后端状态与页面状态乱序。 */
  const enqueue = useCallback((operation: () => Promise<void>) => {
    pending.current = pending.current.catch(() => undefined).then(async () => {
      await initialized.current
      await operation()
      setError(null)
    }).catch(error => {
      console.warn('保存收藏失败', error)
      setError('收藏保存失败，请刷新页面后重试。')
    })
  }, [])

  const addFavorite = useCallback((url: string, title: string) => {
    enqueue(async () => {
      const response = await fetch('/api/favorites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, title }),
      })
      if (!response.ok) throw new Error('新增收藏失败')
      const saved = await response.json() as { url: string, title: string, timestamp: number }
      update({ ...current.current, [saved.url]: { title: saved.title, timestamp: saved.timestamp } })
    })
  }, [enqueue, update])

  const removeFavorite = useCallback((url: string) => {
    enqueue(async () => {
      const response = await fetch(`/api/favorites?url=${encodeURIComponent(url)}`, {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('取消收藏失败')
      const next = { ...current.current }
      delete next[url]
      update(next)
    })
  }, [enqueue, update])

  const toggleFavorite = useCallback((url: string, title: string) => {
    // 在队列执行时判断最新状态，避免连续点击都按旧状态操作。
    enqueue(async () => {
      if (url in current.current) {
        const response = await fetch(`/api/favorites?url=${encodeURIComponent(url)}`, {
          method: 'DELETE',
        })
        if (!response.ok) throw new Error('取消收藏失败')
        const next = { ...current.current }
        delete next[url]
        update(next)
      } else {
        const response = await fetch('/api/favorites', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url, title }),
        })
        if (!response.ok) throw new Error('新增收藏失败')
        const saved = await response.json() as { url: string, title: string, timestamp: number }
        update({ ...current.current, [saved.url]: { title: saved.title, timestamp: saved.timestamp } })
      }
    })
  }, [enqueue, update])

  const isFavorite = useCallback((url: string) => url in favorites, [favorites])

  const clearAll = useCallback(() => {
    enqueue(async () => {
      const response = await fetch('/api/favorites/all', { method: 'DELETE' })
      if (!response.ok) throw new Error('清空收藏失败')
      update({})
    })
  }, [enqueue, update])

  return {
    favorites,
    addFavorite,
    removeFavorite,
    toggleFavorite,
    isFavorite,
    clearAll,
    favoriteCount: Object.keys(favorites).length,
    error,
  }
}

// 原版来源弹窗沿用卡片布局，描述和订阅列表改为 SpiderAI 的真实快照来源。
import { X, Rss, Globe, CheckCircle, XCircle, Clock, ExternalLink } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { SiteStat } from '../types'

interface SourceModalProps {
  isOpen: boolean
  onClose: () => void
  siteStats: SiteStat[]
  sourceCount: number
  windowHours: number
}

interface SourceStatus {
  generated_at: string
  sites: {
    site_id: string
    site_name: string
    ok: boolean
    item_count: number
    duration_ms: number
    error: string | null
  }[]
  successful_sites: number
  failed_sites: string[]
}

interface OpmlGroup {
  name: string
  feeds: {
    name: string
    url: string
  }[]
}

const SITE_INFO: Record<string, { description: string; url: string }> = {
  rss: { description: '通过 RSS 或 Atom 收录的资讯。', url: '' },
  wechat: { description: '通过公众号 RSS 转换服务收录的资讯。', url: '' },
  url: { description: '通过静态文章网页收录的资讯。', url: '' },
}

/** 展示快照中的来源分类、实际订阅名和失败来源。 */
export function SourceModal({ isOpen, onClose, siteStats, sourceCount, windowHours }: SourceModalProps) {
  const [sourceStatus, setSourceStatus] = useState<SourceStatus | null>(null)
  const [opmlGroups, setOpmlGroups] = useState<OpmlGroup[]>([])

  useEffect(() => {
    if (isOpen) {
      const basePath = import.meta.env.BASE_URL || '/'
      fetch(`${basePath}data/source-status.json`)
        .then(res => res.json())
        .then(data => setSourceStatus(data))
        .catch(() => {})
      
      // 来源列表按当前时间范围请求，避免与顶部来源数量不一致。
      const range = windowHours === 24 ? '24h' : '7d'
      fetch(`${basePath}data/opml-feeds.json?range=${range}`)
        .then(res => res.json())
        .then(data => setOpmlGroups(data))
        .catch(() => {})
    }
  }, [isOpen, windowHours])

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const totalRawItems = siteStats.reduce((sum, s) => sum + s.raw_count, 0)
  const totalFilteredItems = siteStats.reduce((sum, s) => sum + s.count, 0)
  const sortedSiteStats = [...siteStats]

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-hidden animate-fade-in">
        <div className="sticky top-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Rss className="w-5 h-5 text-primary-500" />
              数据源概览
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              收录 {siteStats.length} 类来源 · {sourceCount} 个订阅源
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
          >
            <X className="w-5 h-5 text-slate-500" />
          </button>
        </div>

        <div className="px-6 py-4 overflow-y-auto max-h-[calc(85vh-80px)]">
          <div className="grid grid-cols-3 gap-3 mb-6">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{siteStats.length}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">来源分类</p>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{sourceCount}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">订阅源</p>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4 text-center">
              <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{totalRawItems.toLocaleString()}</p>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">本次收录</p>
            </div>
          </div>

          <div className="bg-slate-50 dark:bg-slate-900/50 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
              <Clock className="w-4 h-4" />
              <span>最近 <strong className="text-slate-900 dark:text-white">{windowHours} 小时</strong> 内，快照中有 <strong className="text-slate-900 dark:text-white">{totalFilteredItems.toLocaleString()}</strong> 条资讯</span>
            </div>
          </div>

          <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 flex items-center gap-2">
            <Globe className="w-4 h-4" />
            来源分类详情
          </h3>
          
          <div className="space-y-3">
            {sortedSiteStats.map((stat) => {
              const siteInfo = sourceStatus?.sites.find(s => s.site_id === stat.site_id)
              const isOk = siteInfo?.ok !== false
              const info = SITE_INFO[stat.site_id]
              const groupFeeds = opmlGroups.find(g => g.name === stat.site_id)?.feeds || []
              
              return (
                <div key={stat.site_id} className="rounded-lg border border-slate-200 dark:border-slate-600 overflow-hidden">
                  <div className="flex items-center justify-between p-3 bg-white dark:bg-slate-700/50">
                    <div className="flex items-center gap-3">
                      {isOk ? (
                        <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                      )}
                      <div className="text-left">
                        <span className="font-medium text-slate-900 dark:text-white">{stat.site_name}</span>
                        {groupFeeds.length > 0 && (
                          <span className="ml-2 text-xs text-slate-500">({groupFeeds.length} 个来源)</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-slate-500 dark:text-slate-400">
                        收录: <span className="text-primary-600 dark:text-primary-400 font-medium">{stat.count}</span>
                      </span>
                    </div>
                  </div>
                  
                  <div className="px-4 pb-4 pt-2 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-200 dark:border-slate-600">
                    {info && (
                      <div className="mb-3">
                        <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">{info.description}</p>
                        {info.url && (
                          <a
                            href={info.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-primary-500 hover:text-primary-600"
                          >
                            <ExternalLink className="w-3 h-3" />
                            {info.url}
                          </a>
                        )}
                      </div>
                    )}
                    
                    {groupFeeds.length > 0 && (
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 mt-2">
                        {groupFeeds.map((feed, idx) => (
                          <div
                            key={idx}
                            className="text-xs text-slate-600 dark:text-slate-400 truncate py-1 px-2 bg-white dark:bg-slate-700/50 rounded border border-slate-200 dark:border-slate-600"
                            title={feed.name}
                          >
                            {feed.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {sourceStatus?.failed_sites && sourceStatus.failed_sites.length > 0 && (
            <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl">
              <h4 className="text-sm font-medium text-red-700 dark:text-red-400 mb-2">抓取失败的数据源</h4>
              <p className="text-xs text-red-600 dark:text-red-300">
                {sourceStatus.failed_sites.join('、')}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

-- 文章链接在本地库内唯一，首次发现时间在重复采集时保持不变。
CREATE TABLE IF NOT EXISTS articles (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    published_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    effective_at TEXT NOT NULL,
    rank_score REAL,
    payload_json TEXT NOT NULL
);

-- 按文章实际展示时间检索，避免每次请求扫描完整历史。
CREATE INDEX IF NOT EXISTS idx_articles_effective_at ON articles(effective_at DESC);

-- 采集批次保留最新错误信息；快照哈希防止重复导入产生重复批次。
CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_hash TEXT NOT NULL UNIQUE,
    collected_at TEXT NOT NULL,
    errors_json TEXT NOT NULL
);

-- 收藏独立于文章保存；过期文章只有在对应链接未收藏时才可清理。
CREATE TABLE IF NOT EXISTS favorites (
    url TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    timestamp_ms INTEGER NOT NULL
);

-- 记录浏览器旧收藏是否已迁移及上次清理时间，重启后继续按周期执行。
CREATE TABLE IF NOT EXISTS maintenance (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

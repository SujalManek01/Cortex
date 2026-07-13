import { useEffect, useState } from 'react'
import { getApplications, getFolders, getWebsites } from '../api/cortexApi'
import type { ApplicationItem, FolderItem, WebsiteItem } from '../types/cortex'

export function RegistryPanels() {
  const [apps, setApps] = useState<ApplicationItem[]>([])
  const [folders, setFolders] = useState<FolderItem[]>([])
  const [websites, setWebsites] = useState<WebsiteItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const [appRes, folderRes, webRes] = await Promise.all([
          getApplications(),
          getFolders(),
          getWebsites(),
        ])
        setApps(appRes.applications)
        setFolders(folderRes.folders)
        setWebsites(webRes.websites)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch registries.')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) {
    return <div className="card"><div className="card-header"><span className="spinner"></span> Loading Registries...</div></div>
  }

  if (error) {
    return <div className="card"><div className="error-banner">{error}</div></div>
  }

  return (
    <div className="registry-panels">
      <div className="card">
        <div className="card-header">
          <span className="card-icon">🖥️</span>
          <h3 className="card-title">Applications</h3>
        </div>
        <ul className="registry-list">
          {apps.map(app => (
            <li key={app.alias}>
              <strong>{app.alias}</strong> ({app.name})
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-icon">📁</span>
          <h3 className="card-title">Folders</h3>
        </div>
        <ul className="registry-list">
          {folders.map(folder => (
            <li key={folder.alias}>
              <strong>{folder.alias}</strong> <span title={folder.path} className="registry-path">{folder.path.split('\\').pop()}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-icon">🌐</span>
          <h3 className="card-title">Websites</h3>
        </div>
        <ul className="registry-list">
          {websites.map(web => (
            <li key={web.alias}>
              <strong>{web.alias}</strong> <span title={web.url} className="registry-path">{web.url.replace(/^https?:\/\//, '')}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

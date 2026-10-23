import { Fragment, type ReactNode } from 'react'

/** Render a heading's inline text, honoring **bold** and `code`. */
function inline(text: string, keyBase: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g)
  return parts.filter(Boolean).map((part, i) => {
    const key = `${keyBase}-${i}`
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={key}>{part.slice(2, -2)}</strong>
    if (part.startsWith('`') && part.endsWith('`')) return <code key={key} className="rounded-[5px] bg-surface-2 px-1.5 py-0.5 text-[0.9em]">{part.slice(1, -1)}</code>
    if (part.startsWith('*') && part.endsWith('*')) return <em key={key}>{part.slice(1, -1)}</em>
    return <Fragment key={key}>{part}</Fragment>
  })
}

/**
 * Minimal Markdown renderer for lesson bodies.
 *
 * Deliberately small and dependency-free: headings, paragraphs, bullet and
 * numbered lists, blockquotes, fenced code, and inline bold/italic/code. It
 * escapes nothing because React already escapes all text nodes — raw HTML is
 * never injected, which keeps lesson content safe to render.
 */
export function Markdown({ source, className }: { source: string; className?: string }) {
  const blocks: ReactNode[] = []
  const lines = (source ?? '').replace(/\r\n/g, '\n').split('\n')
  let i = 0
  let key = 0

  while (i < lines.length) {
    const line = lines[i]

    // Fenced code block
    if (/^```/.test(line)) {
      const lang = line.slice(3).trim()
      const body: string[] = []
      i++
      while (i < lines.length && !/^```/.test(lines[i])) {
        body.push(lines[i])
        i++
      }
      i++ // closing fence
      blocks.push(
        <pre key={key++} className="overflow-x-auto rounded-tile bg-fg/95 p-4 text-[13px] leading-relaxed text-white/90">
          <code data-lang={lang}>{body.join('\n')}</code>
        </pre>,
      )
      continue
    }

    // Blank line
    if (!line.trim()) {
      i++
      continue
    }

    // Heading
    const heading = /^(#{1,4})\s+(.*)$/.exec(line)
    if (heading) {
      const depth = heading[1].length
      const size = depth === 1 ? 'text-[22px]' : depth === 2 ? 'text-[18px]' : depth === 3 ? 'text-[16px]' : 'text-[15px]'
      blocks.push(
        <p key={key++} className={`mt-6 font-semibold tracking-tight first:mt-0 ${size}`}>
          {inline(heading[2], `h${key}`)}
        </p>,
      )
      i++
      continue
    }

    // Blockquote
    if (/^>\s?/.test(line)) {
      const body: string[] = []
      while (i < lines.length && /^>\s?/.test(lines[i])) {
        body.push(lines[i].replace(/^>\s?/, ''))
        i++
      }
      blocks.push(
        <blockquote key={key++} className="border-l-2 border-accent/40 bg-accent-soft/40 py-2 pl-4 text-[14px] text-muted">
          {body.map((b, bi) => (
            <p key={bi}>{inline(b, `q${key}-${bi}`)}</p>
          ))}
        </blockquote>,
      )
      continue
    }

    // Bullet list
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ''))
        i++
      }
      blocks.push(
        <ul key={key++} className="mt-3 flex flex-col gap-1.5 pl-5 text-[14.5px] leading-relaxed [&>li]:list-disc [&>li]:marker:text-accent">
          {items.map((item, ii) => (
            <li key={ii}>{inline(item, `l${key}-${ii}`)}</li>
          ))}
        </ul>,
      )
      continue
    }

    // Numbered list
    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ''))
        i++
      }
      blocks.push(
        <ol key={key++} className="mt-3 flex flex-col gap-1.5 pl-5 text-[14.5px] leading-relaxed [&>li]:list-decimal [&>li]:marker:text-accent marker:font-medium">
          {items.map((item, ii) => (
            <li key={ii}>{inline(item, `o${key}-${ii}`)}</li>
          ))}
        </ol>,
      )
      continue
    }

    // Paragraph: gather consecutive plain lines
    const para: string[] = []
    while (i < lines.length && lines[i].trim() && !/^(#{1,4}\s|```|[-*]\s|\d+\.\s|>\s?)/.test(lines[i])) {
      para.push(lines[i])
      i++
    }
    blocks.push(
      <p key={key++} className="mt-3 text-[14.5px] leading-[1.7] first:mt-0">
        {inline(para.join(' '), `p${key}`)}
      </p>,
    )
  }

  return <div className={className}>{blocks}</div>
}

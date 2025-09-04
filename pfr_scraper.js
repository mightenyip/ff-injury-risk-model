(() => {
  // Infer season & player id from URL
  const url = new URL(location.href);
  const seasonMatch = url.pathname.match(/gamelog\/(\d{4})/);
  const season = seasonMatch ? seasonMatch[1] : (new Date().getFullYear() + '');
  const pid = url.pathname.split('/')[3]?.toLowerCase() || 'player';

  // Find a table that's sometimes hidden inside HTML comments
  function findCommentedTable(candidateIds) {
    for (const id of candidateIds) {
      const container = document.getElementById('all_' + id) || document;
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_COMMENT, null);
      let node;
      while ((node = walker.nextNode())) {
        if (node.nodeValue.includes(`id="${id}"`)) {
          const div = document.createElement('div');
          div.innerHTML = node.nodeValue;
          const tbl = div.querySelector(`table#${id}`);
          if (tbl) return tbl;
        }
      }
      const live = document.querySelector(`table#${id}`);
      if (live) return live;
    }
    // Fallback: any game-loggy table
    return document.querySelector(
      'table#rushing_and_receiving, table#receiving_and_rushing, table#passing, table#receiving, table#defense'
    );
  }

  const table = findCommentedTable([
    'rushing_and_receiving', 'receiving_and_rushing', 'passing', 'receiving', 'defense'
  ]);
  if (!table) { console.warn('PFR: game-log table not found'); return; }

  // Build CSV (skip repeated header rows inside tbody)
  const clean = s => (s || '').replace(/\s+/g, ' ').trim().replace(/"/g, '""');
  const thead = [...table.querySelectorAll('thead tr')].pop();
  const header = thead ? [...thead.children].map(c => `"${clean(c.innerText)}"`).join(',') + '\n' : '';

  const rows = [...table.querySelectorAll('tbody tr')].filter(tr => !tr.classList.contains('thead'));
  const body = rows.map(tr => {
    const cells = [...tr.querySelectorAll('th,td')];
    return cells.map(c => `"${clean(c.innerText)}"`).join(',');
  }).join('\n');

  const csv = header + body + '\n';
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(blob),
    download: `${pid}_${season}_gamelog.csv`
  });
  document.body.appendChild(a); a.click(); URL.revokeObjectURL(a.href); a.remove();
})();
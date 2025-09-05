// Debug version of the PFR scraper bookmarklet
// This version will show more information in the console

javascript:(() => {
  console.log('PFR Scraper: Starting...');
  
  // Infer season & player id from URL
  const url = new URL(location.href);
  console.log('Current URL:', url.href);
  
  const seasonMatch = url.pathname.match(/gamelog\/(\d{4})/);
  const season = seasonMatch ? seasonMatch[1] : (new Date().getFullYear() + '');
  const pid = url.pathname.split('/')[3]?.toLowerCase() || 'player';
  
  console.log('Detected season:', season);
  console.log('Detected player ID:', pid);
  
  // Find a table that's sometimes hidden inside HTML comments
  function findCommentedTable(candidateIds) {
    console.log('Looking for tables with IDs:', candidateIds);
    
    for (const id of candidateIds) {
      const container = document.getElementById('all_' + id) || document;
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_COMMENT, null);
      let node;
      
      while ((node = walker.nextNode())) {
        if (node.nodeValue.includes(`id="${id}"`)) {
          console.log('Found table in comment:', id);
          const div = document.createElement('div');
          div.innerHTML = node.nodeValue;
          const tbl = div.querySelector(`table#${id}`);
          if (tbl) return tbl;
        }
      }
      
      const live = document.querySelector(`table#${id}`);
      if (live) {
        console.log('Found live table:', id);
        return live;
      }
    }
    
    // Fallback: any game-loggy table
    const fallback = document.querySelector(
      'table#rushing_and_receiving, table#receiving_and_rushing, table#passing, table#receiving, table#defense'
    );
    
    if (fallback) {
      console.log('Found fallback table:', fallback.id);
    } else {
      console.log('No fallback table found');
    }
    
    return fallback;
  }
  
  const table = findCommentedTable([
    'rushing_and_receiving', 'receiving_and_rushing', 'passing', 'receiving', 'defense'
  ]);
  
  if (!table) {
    console.warn('PFR: game-log table not found');
    console.log('Available tables on page:');
    const allTables = document.querySelectorAll('table');
    allTables.forEach((t, i) => {
      console.log(`Table ${i}: id="${t.id}", class="${t.className}"`);
    });
    return;
  }
  
  console.log('Found table:', table.id);
  console.log('Table rows:', table.querySelectorAll('tbody tr').length);
  
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
  console.log('Generated CSV length:', csv.length);
  console.log('First 200 chars of CSV:', csv.substring(0, 200));
  
  const blob = new Blob([csv], { type: 'text/csv' });
  const filename = `${pid}_${season}_gamelog.csv`;
  console.log('Downloading file:', filename);
  
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(blob),
    download: filename
  });
  
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(a.href);
  a.remove();
  
  console.log('Download initiated for:', filename);
})();

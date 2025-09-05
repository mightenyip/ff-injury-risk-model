// Improved PFR scraper that finds tables more reliably
javascript:(() => {
  console.log('PFR Scraper: Starting improved version...');
  
  // Get URL info
  const url = new URL(location.href);
  const seasonMatch = url.pathname.match(/gamelog\/(\d{4})/);
  const season = seasonMatch ? seasonMatch[1] : (new Date().getFullYear() + '');
  const pid = url.pathname.split('/')[3]?.toLowerCase() || 'player';
  
  console.log('Season:', season, 'Player ID:', pid);
  
  // More comprehensive table finder
  function findGameLogTable() {
    // First, try to find any table with game data
    const allTables = document.querySelectorAll('table');
    console.log('Found', allTables.length, 'total tables');
    
    // Look for tables that might contain game logs
    const candidates = [];
    
    allTables.forEach((table, i) => {
      const id = table.id || '';
      const className = table.className || '';
      const text = table.innerText || '';
      
      // Check if this looks like a game log table
      const hasGameData = text.includes('Week') || text.includes('Date') || text.includes('Opp') || text.includes('Rush') || text.includes('Rec');
      const hasStats = text.includes('Yds') || text.includes('TD') || text.includes('Att');
      
      if (hasGameData || hasStats) {
        candidates.push({
          table: table,
          id: id,
          className: className,
          score: (hasGameData ? 2 : 0) + (hasStats ? 1 : 0) + (id.includes('rushing') || id.includes('receiving') ? 3 : 0)
        });
        console.log(`Candidate ${i}: id="${id}", class="${className}", score=${(hasGameData ? 2 : 0) + (hasStats ? 1 : 0) + (id.includes('rushing') || id.includes('receiving') ? 3 : 0)}`);
      }
    });
    
    // Sort by score and return the best candidate
    candidates.sort((a, b) => b.score - a.score);
    
    if (candidates.length > 0) {
      console.log('Selected table:', candidates[0].id, 'with score:', candidates[0].score);
      return candidates[0].table;
    }
    
    // Fallback: return the largest table (most likely to be the main data table)
    let largestTable = null;
    let maxRows = 0;
    
    allTables.forEach(table => {
      const rows = table.querySelectorAll('tr').length;
      if (rows > maxRows) {
        maxRows = rows;
        largestTable = table;
      }
    });
    
    console.log('Using largest table with', maxRows, 'rows');
    return largestTable;
  }
  
  const table = findGameLogTable();
  
  if (!table) {
    console.error('No suitable table found!');
    alert('No game log table found on this page. Make sure you are on a player\'s game log page.');
    return;
  }
  
  console.log('Using table with ID:', table.id);
  
  // Extract data from table
  const clean = s => (s || '').replace(/\s+/g, ' ').trim().replace(/"/g, '""');
  
  // Get headers
  const headerRow = table.querySelector('thead tr') || table.querySelector('tr');
  const headers = headerRow ? [...headerRow.querySelectorAll('th, td')].map(c => clean(c.innerText)) : [];
  
  // Get data rows (skip header rows)
  const dataRows = [...table.querySelectorAll('tbody tr, tr')].filter(tr => {
    const cells = tr.querySelectorAll('th, td');
    return cells.length > 0 && !tr.classList.contains('thead');
  });
  
  console.log('Found', headers.length, 'columns and', dataRows.length, 'data rows');
  
  // Build CSV
  const csvRows = [];
  
  // Add header
  if (headers.length > 0) {
    csvRows.push(headers.map(h => `"${h}"`).join(','));
  }
  
  // Add data rows
  dataRows.forEach(row => {
    const cells = [...row.querySelectorAll('th, td')];
    const rowData = cells.map(cell => `"${clean(cell.innerText)}"`).join(',');
    csvRows.push(rowData);
  });
  
  const csv = csvRows.join('\n') + '\n';
  console.log('Generated CSV with', csvRows.length, 'rows');
  
  // Create and download file
  const blob = new Blob([csv], { type: 'text/csv' });
  const filename = `${pid}_${season}_gamelog.csv`;
  
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.style.display = 'none';
  
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
  
  console.log('Downloaded:', filename);
  alert(`Downloaded ${filename} with ${dataRows.length} games`);
})();

// Targeted PFR scraper that looks specifically for game log tables
javascript:(() => {
  console.log('PFR Scraper: Looking for game log table...');
  
  // Get URL info
  const url = new URL(location.href);
  const seasonMatch = url.pathname.match(/gamelog\/(\d{4})/);
  const season = seasonMatch ? seasonMatch[1] : (new Date().getFullYear() + '');
  const pid = url.pathname.split('/')[3]?.toLowerCase() || 'player';
  
  console.log('Season:', season, 'Player ID:', pid);
  
  // Look specifically for game log tables
  function findGameLogTable() {
    // First, try the specific IDs that PFR uses for game logs
    const specificIds = [
      'rushing_and_receiving',
      'receiving_and_rushing', 
      'rushing',
      'receiving',
      'passing'
    ];
    
    for (const id of specificIds) {
      // Check for table in comments (PFR often hides tables this way)
      const container = document.getElementById('all_' + id);
      if (container) {
        const walker = document.createTreeWalker(container, NodeFilter.SHOW_COMMENT, null);
        let node;
        while ((node = walker.nextNode())) {
          if (node.nodeValue.includes(`id="${id}"`)) {
            const div = document.createElement('div');
            div.innerHTML = node.nodeValue;
            const table = div.querySelector(`table#${id}`);
            if (table) {
              console.log('Found table in comments:', id);
              return table;
            }
          }
        }
      }
      
      // Check for live table
      const liveTable = document.querySelector(`table#${id}`);
      if (liveTable) {
        console.log('Found live table:', id);
        return liveTable;
      }
    }
    
    // If no specific table found, look for tables with game log characteristics
    const allTables = document.querySelectorAll('table');
    console.log('Checking', allTables.length, 'tables for game log characteristics...');
    
    for (let i = 0; i < allTables.length; i++) {
      const table = allTables[i];
      const text = table.innerText.toLowerCase();
      
      // Look for specific game log indicators
      const hasWeek = text.includes('week') || text.includes('wk');
      const hasDate = text.includes('date');
      const hasOpp = text.includes('opp') || text.includes('opponent');
      const hasRush = text.includes('rush') || text.includes('att');
      const hasRec = text.includes('rec') || text.includes('target');
      const hasYds = text.includes('yds') || text.includes('yards');
      const hasTd = text.includes('td') || text.includes('touchdown');
      
      // Count how many game log indicators this table has
      const indicators = [hasWeek, hasDate, hasOpp, hasRush, hasRec, hasYds, hasTd];
      const score = indicators.filter(Boolean).length;
      
      console.log(`Table ${i}: id="${table.id}", score=${score}`, {
        week: hasWeek, date: hasDate, opp: hasOpp, 
        rush: hasRush, rec: hasRec, yds: hasYds, td: hasTd
      });
      
      // If this table has at least 4 game log indicators, it's probably the right one
      if (score >= 4) {
        console.log('Selected table with score:', score);
        return table;
      }
    }
    
    console.log('No suitable game log table found');
    return null;
  }
  
  const table = findGameLogTable();
  
  if (!table) {
    console.error('No game log table found!');
    alert('No game log table found. Make sure you are on a player\'s game log page.');
    return;
  }
  
  console.log('Using table with ID:', table.id);
  
  // Extract data more carefully
  const clean = s => (s || '').replace(/\s+/g, ' ').trim().replace(/"/g, '""');
  
  // Find the header row
  let headerRow = null;
  const thead = table.querySelector('thead');
  if (thead) {
    headerRow = thead.querySelector('tr');
  } else {
    // Look for the first row that looks like a header
    const rows = table.querySelectorAll('tr');
    for (const row of rows) {
      const cells = row.querySelectorAll('th, td');
      if (cells.length > 0) {
        const firstCell = cells[0].innerText.toLowerCase();
        if (firstCell.includes('week') || firstCell.includes('date') || firstCell.includes('game')) {
          headerRow = row;
          break;
        }
      }
    }
  }
  
  if (!headerRow) {
    console.error('No header row found');
    alert('Could not find table headers');
    return;
  }
  
  // Extract headers
  const headers = [...headerRow.querySelectorAll('th, td')].map(c => clean(c.innerText));
  console.log('Headers:', headers);
  
  // Find data rows (skip header rows)
  const allRows = [...table.querySelectorAll('tr')];
  const dataRows = allRows.filter((row, index) => {
    // Skip the header row
    if (row === headerRow) return false;
    
    // Skip rows that look like headers (contain "Week", "Date", etc. in first cell)
    const firstCell = row.querySelector('th, td');
    if (firstCell) {
      const text = firstCell.innerText.toLowerCase();
      if (text.includes('week') || text.includes('date') || text.includes('game')) {
        return false;
      }
    }
    
    // Skip empty rows
    const cells = row.querySelectorAll('th, td');
    return cells.length > 0;
  });
  
  console.log('Found', dataRows.length, 'data rows');
  
  // Build CSV
  const csvRows = [];
  
  // Add header
  csvRows.push(headers.map(h => `"${h}"`).join(','));
  
  // Add data rows
  dataRows.forEach((row, index) => {
    const cells = [...row.querySelectorAll('th, td')];
    const rowData = cells.map(cell => `"${clean(cell.innerText)}"`).join(',');
    csvRows.push(rowData);
    
    // Log first few rows for debugging
    if (index < 3) {
      console.log(`Row ${index + 1}:`, cells.map(c => c.innerText.trim()));
    }
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
  alert(`Downloaded ${filename} with ${dataRows.length} games and ${headers.length} columns`);
})();

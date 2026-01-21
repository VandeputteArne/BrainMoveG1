import ExcelJS from 'exceljs';

/**
 * Composable for exporting game results to Excel
 * @param {Object} options - Export configuration
 * @param {Array} options.stats - Statistics array
 * @param {Array} options.counts - Counts array (correct, fout, te laat)
 * @param {Array} options.rounds - Rounds data for chart
 * @param {string} options.username - Username for the export
 */
export async function exportToExcel({ stats, counts, rounds, username }) {
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('Resultaten');

  try {
    const logoResponse = await fetch('/images/BrainMove-Logo.png');
    if (logoResponse.ok) {
      const logoBlob = await logoResponse.blob();
      const arrayBuffer = await logoBlob.arrayBuffer();

      const imageId = workbook.addImage({
        buffer: arrayBuffer,
        extension: 'png',
      });

      worksheet.getRow(1).height = 30;
      worksheet.getRow(2).height = 30;

      const logoWidth = 120;
      const logoHeight = logoWidth / (594 / 502); // ≈ 101

      worksheet.addImage(imageId, {
        tl: { col: 0, row: 0 },
        ext: { width: logoWidth, height: logoHeight },
        editAs: 'absolute',
      });
    }
  } catch (e) {
    console.warn('Logo could not be added:', e);
  }

  worksheet.mergeCells('A4:D4');
  const titleCell = worksheet.getCell('A4');
  titleCell.value = 'Resultaten Overzicht';
  titleCell.font = { size: 18, bold: true, color: { argb: 'FF2979FF' } };
  titleCell.alignment = { horizontal: 'center', vertical: 'middle' };
  titleCell.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FFE8F4FF' },
  };
  worksheet.getRow(4).height = 30;

  if (username) {
    worksheet.addRow([]);
    const usernameRow = worksheet.addRow(['Gebruiker:', username]);
    usernameRow.getCell(1).font = { bold: true };
    usernameRow.getCell(2).font = { color: { argb: 'FF2979FF' } };
  }

  worksheet.addRow([]);
  worksheet.addRow(['Statistieken']);
  const statsRow = worksheet.lastRow.number;
  worksheet.getCell(`A${statsRow}`).font = { bold: true, size: 14 };

  const statsHeaderRow = worksheet.addRow(['Categorie', 'Waarde']);
  statsHeaderRow.font = { bold: true };
  statsHeaderRow.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FFE8F4FF' },
  };

  stats.forEach((stat) => {
    worksheet.addRow([stat.label, stat.waarde]);
  });

  worksheet.addRow([]);
  worksheet.addRow(['Totale Uitslag']);
  const countsStartRow = worksheet.lastRow.number;
  worksheet.getCell(`A${countsStartRow}`).font = { bold: true, size: 14 };

  const countsHeaderRow = worksheet.addRow(['Type', 'Aantal']);
  countsHeaderRow.font = { bold: true };
  countsHeaderRow.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FFE8F4FF' },
  };

  counts.forEach((count) => {
    const row = worksheet.addRow([count.label, count.value]);
    if (count.type === 'correct') {
      row.getCell(2).font = { color: { argb: 'FF00B709' }, bold: true };
    } else if (count.type === 'fout') {
      row.getCell(2).font = { color: { argb: 'FFF91818' }, bold: true };
    } else if (count.type === 'telaat') {
      row.getCell(2).font = { color: { argb: 'FFFFC400' }, bold: true };
    }
  });

  if (rounds.length) {
    worksheet.addRow([]);
    worksheet.addRow(['Rondes']);
    const roundsStartRow = worksheet.lastRow.number;
    worksheet.getCell(`A${roundsStartRow}`).font = { bold: true, size: 14 };

    const roundsHeaderRow = worksheet.addRow(['Ronde', 'Tijd (s)']);
    roundsHeaderRow.font = { bold: true };
    roundsHeaderRow.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FFE8F4FF' },
    };

    rounds.forEach((r) => {
      worksheet.addRow([r.round, r.time]);
    });
  }

  worksheet.columns = [{ width: 25 }, { width: 15 }, { width: 15 }, { width: 15 }];

  const borderStartRow = username ? 8 : 6;
  worksheet.eachRow((row, rowNumber) => {
    if (rowNumber >= borderStartRow) {
      row.eachCell((cell) => {
        cell.border = {
          top: { style: 'thin' },
          left: { style: 'thin' },
          bottom: { style: 'thin' },
          right: { style: 'thin' },
        };
      });
    }
  });

  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const fileName = username ? `resultaten_${username}_${Date.now()}.xlsx` : `resultaten_${Date.now()}.xlsx`;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

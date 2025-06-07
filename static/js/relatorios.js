document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('exportCsv').addEventListener('click', () => {
        let csv = 'Código,Produto,Categoria,Estoque,Preço,Status\n';
        document.querySelectorAll('.report-table tbody tr:not(.no-data)').forEach(row => {
            const cells = row.querySelectorAll('td');
            csv += `"${cells[0].textContent}","${cells[1].textContent}","${cells[2].textContent}",`;
            csv += `"${cells[3].textContent}","${cells[4].textContent}","${cells[5].textContent.trim()}"\n`;
        });
        downloadFile(csv, 'produtos', 'csv');
    });

    document.getElementById('exportPdf').addEventListener('click', () => {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        doc.setFontSize(10).text('Produtos - QuantumStock', 10, 10);
        
        const headers = [['Código', 'Produto', 'Categoria', 'Estoque', 'Preço', 'Status']];
        const rows = [];
        
        document.querySelectorAll('.report-table tbody tr:not(.no-data)').forEach(row => {
            const cells = row.querySelectorAll('td');
            rows.push([
                cells[0].textContent,
                cells[1].textContent,
                cells[2].textContent,
                cells[3].textContent,
                cells[4].textContent,
                cells[5].textContent.trim()
            ]);
        });
        
        doc.autoTable({
            head: headers,
            body: rows,
            startY: 15,
            styles: { fontSize: 7, cellPadding: 1 },
            headStyles: { fillColor: [157, 47, 212], textColor: 255, fontSize: 8 }
        });
        
        doc.save(`produtos_${getDate()}.pdf`);
    });

    document.getElementById('exportActivitiesCsv').addEventListener('click', () => {
        let csv = 'Data,Hora,Ação,Usuário,Detalhes\n';
        document.querySelectorAll('.activity-item').forEach(activity => {
            const user = activity.querySelector('.activity-text strong').textContent;
            const [date, time] = activity.querySelector('.activity-time').textContent.split(' ');
            const details = activity.querySelector('.activity-text').textContent.replace(user, '').trim();
            const action = getAction(activity.querySelector('.activity-icon i'));
            
            csv += `"${date}","${time}","${action}","${user}","${details}"\n`;
        });
        downloadFile(csv, 'atividades', 'csv');
    });

    document.getElementById('exportActivitiesPdf').addEventListener('click', () => {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        doc.setFontSize(9).text('Atividades - QuantumStock', 10, 8);
        
        const rows = [];
        document.querySelectorAll('.activity-item').forEach(activity => {
            const user = activity.querySelector('.activity-text strong').textContent;
            const [date, time] = activity.querySelector('.activity-time').textContent.split(' ');
            let details = activity.querySelector('.activity-text').textContent.replace(user, '').trim();
            const action = getAction(activity.querySelector('.activity-icon i'));
            
            rows.push({
                date,
                time,
                action,
                user: user.length > 10 ? user.substring(0, 8) + '...' : user,
                details: {
                    content: details.length > 60 ? details.substring(0, 57) + '...' : details,
                    styles: { fontSize: details.length > 40 ? 6 : 7 }
                }
            });
        });
        
        doc.autoTable({
            startY: 12,
            columnStyles: {
                0: { cellWidth: 20, fontSize: 7 }, 
                1: { cellWidth: 15, fontSize: 7 }, 
                2: { cellWidth: 15, fontSize: 7 }, 
                3: { cellWidth: 25, fontSize: 7 }, 
                4: { cellWidth: 'auto', fontSize: 7 } 
            },
            body: rows.map(r => [r.date, r.time, r.action, r.user, r.details]),
            styles: { fontSize: 7, cellPadding: 0.5, overflow: 'linebreak' },
            margin: { left: 5, right: 5 }
        });
        
        doc.save(`atividades_${getDate()}.pdf`);
    });

    document.getElementById('printActivities').addEventListener('click', () => {
        const printContent = `
            <style>
                @page { size: auto; margin: 1mm; }
                body { font-family: Arial; font-size: 7px; padding: 0; }
                .activity-grid {
                    display: grid;
                    grid-template-columns: 15px 12px 18px 22px auto;
                    gap: 2px;
                    margin-bottom: 1px;
                }
                .activity-time { color: #666; white-space: nowrap; }
                .activity-text { 
                    overflow: hidden;
                    text-overflow: ellipsis;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                }
            </style>
            <div>${Array.from(document.querySelectorAll('.activity-item')).map(activity => {
                const user = activity.querySelector('.activity-text strong').textContent;
                const [date, time] = activity.querySelector('.activity-time').textContent.split(' ');
                const details = activity.querySelector('.activity-text').textContent.replace(user, '').trim();
                const action = getAction(activity.querySelector('.activity-icon i'));
                
                return `
                    <div class="activity-grid">
                        <div>${date}</div>
                        <div class="activity-time">${time}</div>
                        <div>${action}</div>
                        <div>${user.length > 8 ? user.substring(0,6)+'...' : user}</div>
                        <div class="activity-text">${details}</div>
                    </div>
                `;
            }).join('')}</div>
            <div style="font-size:6px;text-align:right">${new Date().toLocaleString()}</div>
        `;
        
        const win = window.open('', '_blank');
        win.document.write(printContent);
        win.document.close();
        setTimeout(() => win.print(), 50);
    });

    function downloadFile(content, name, type) {
        const blob = new Blob(
            [type === 'csv' ? '\uFEFF' + content : content], 
            { type: type === 'csv' ? 'text/csv;charset=utf-8;' : 'application/pdf' }
        );
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `${name}_${getDate()}.${type}`;
        link.click();
    }

    function getAction(icon) {
        const iconClass = icon.className.split('fa-')[1].split(' ')[0];
        const actions = {
            'edit': 'Editar', 'plus': 'Criar', 'trash': 'Remover',
            'sign-in-alt': 'Login', 'sign-out-alt': 'Logout'
        };
        return actions[iconClass] || 'Ação';
    }

    function getDate() {
        return new Date().toISOString().slice(0, 10).replace(/-/g, '');
    }
});
document.addEventListener('DOMContentLoaded', function() {
    const addSupplierBtn = document.getElementById('addSupplierBtn');
    const supplierModal = document.getElementById('supplierModal');
    const closeModal = document.querySelector('.close-modal');
    const supplierForm = document.getElementById('supplierForm');
    const supplierPhone = document.getElementById('supplierPhone');
    
    const suppliersTable = document.getElementById('suppliersTable');
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const statusFilter = document.getElementById('statusFilter');
    const applyFilters = document.getElementById('applyFilters');
    
    if (supplierPhone) {
        supplierPhone.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 2) {
                value = `(${value.substring(0,2)}) ${value.substring(2)}`;
            }
            if (value.length > 10) {
                value = `${value.substring(0,10)}-${value.substring(10,14)}`;
            }
            
            e.target.value = value;
        });
    }
    
    if (addSupplierBtn) {
        addSupplierBtn.addEventListener('click', function() {
            document.getElementById('modalTitle').textContent = 'Adicionar Novo Fornecedor';
            document.getElementById('supplierId').value = '';
            supplierForm.reset();
            supplierModal.style.display = 'flex';
        });
    }
    
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            supplierModal.style.display = 'none';
        });
    }
    
    window.addEventListener('click', function(event) {
        if (event.target === supplierModal) {
            supplierModal.style.display = 'none';
        }
    });
    
    if (supplierForm) {
        supplierForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const phone = document.getElementById('supplierPhone').value;
            const phoneRegex = /^\(\d{2}\) \d{4,5}-\d{4}$/;
            
            if (!phoneRegex.test(phone)) {
                showAlert('error', 'Formato de telefone inválido! Use (00) 0000-0000 ou (00) 00000-0000');
                return;
            }
            
            const supplierId = document.getElementById('supplierId').value;
            const isEdit = supplierId !== '';
            
            const formData = {
                name: document.getElementById('supplierName').value,
                category: document.getElementById('supplierCategory').value,
                contact: document.getElementById('supplierContact').value,
                email: document.getElementById('supplierEmail').value,
                phone: phone,
                address: document.getElementById('supplierAddress').value,
                city: document.getElementById('supplierCity').value,
                state: document.getElementById('supplierState').value,
                status: document.getElementById('supplierStatus').value
            };
            
            const url = isEdit ? '/update_supplier' : '/add_supplier';
            
            if (isEdit) {
                formData.id = supplierId;
            }
            
            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', isEdit ? 'Fornecedor atualizado com sucesso!' : 'Fornecedor adicionado com sucesso!');
                    supplierModal.style.display = 'none';
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    showAlert('error', data.message || 'Ocorreu um erro. Por favor, tente novamente.');
                }
            })
            .catch(error => {
                showAlert('error', 'Erro na comunicação com o servidor.');
                console.error('Error:', error);
            });
        });
    }
    
    suppliersTable.addEventListener('click', function(e) {
        if (e.target.closest('.edit-btn')) {
            const btn = e.target.closest('.edit-btn');
            const supplierId = btn.getAttribute('data-id');
            
            fetch(`/get_supplier?id=${supplierId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const supplier = data.supplier;
                        
                        document.getElementById('modalTitle').textContent = 'Editar Fornecedor';
                        document.getElementById('supplierId').value = supplierId;
                        
                        document.getElementById('supplierName').value = supplier.name || '';
                        document.getElementById('supplierCategory').value = supplier.category || '';
                        document.getElementById('supplierContact').value = supplier.contact || '';
                        document.getElementById('supplierEmail').value = supplier.email || '';
                        document.getElementById('supplierPhone').value = supplier.phone || '';
                        document.getElementById('supplierAddress').value = supplier.address || '';
                        document.getElementById('supplierCity').value = supplier.city || '';
                        document.getElementById('supplierState').value = supplier.state || '';
                        document.getElementById('supplierStatus').value = supplier.status || 'Ativo';
                        
                        supplierModal.style.display = 'flex';
                    } else {
                        showAlert('error', 'Erro ao carregar dados do fornecedor');
                    }
                })
                .catch(error => {
                    showAlert('error', 'Erro ao carregar dados');
                    console.error('Error:', error);
                });
        }
    });
    
    suppliersTable.addEventListener('click', function(e) {
        if (e.target.closest('.delete-btn')) {
            if (confirm('Tem certeza que deseja excluir este fornecedor?')) {
                const btn = e.target.closest('.delete-btn');
                const supplierId = btn.getAttribute('data-id');
                
                fetch('/delete_supplier', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ id: supplierId })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showAlert('success', 'Fornecedor excluído com sucesso!');
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    } else {
                        showAlert('error', data.message || 'Ocorreu um erro ao excluir o fornecedor.');
                    }
                })
                .catch(error => {
                    showAlert('error', 'Erro na comunicação com o servidor.');
                    console.error('Error:', error);
                });
            }
        }
    });
    
    if (applyFilters) {
        applyFilters.addEventListener('click', function() {
            filterSuppliers();
        });
    }
    
    function filterSuppliers() {
        const searchTerm = searchInput.value.toLowerCase();
        const categoryValue = categoryFilter.value;
        const statusValue = statusFilter.value;
        
        const rows = suppliersTable.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const name = row.cells[1].textContent.toLowerCase();
            const category = row.cells[2].textContent;
            const status = row.cells[5].querySelector('.status-badge').textContent.trim();
            
            const matchesSearch = name.includes(searchTerm);
            const matchesCategory = categoryValue === '' || category === categoryValue;
            const matchesStatus = statusValue === '' || status === statusValue;
            
            if (matchesSearch && matchesCategory && matchesStatus) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        updatePaginationInfo();
    }
    
    function updatePaginationInfo() {
        const visibleRows = suppliersTable.querySelectorAll('tbody tr:not([style*="display: none"])');
        const startItem = document.getElementById('startItem');
        const endItem = document.getElementById('endItem');
        const totalItems = document.getElementById('totalItems');
        
        if (visibleRows.length > 0) {
            startItem.textContent = 1;
            endItem.textContent = Math.min(visibleRows.length, 5);
            totalItems.textContent = visibleRows.length;
        } else {
            startItem.textContent = 0;
            endItem.textContent = 0;
            totalItems.textContent = 0;
        }
    }
    
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.padding = '15px';
        alertDiv.style.borderRadius = '5px';
        alertDiv.style.color = 'white';
        alertDiv.style.backgroundColor = type === 'success' ? '#00b894' : '#d63031';
        alertDiv.style.zIndex = '1000';
        alertDiv.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        alertDiv.style.animation = 'fadeIn 0.3s';
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.style.animation = 'fadeOut 0.3s';
            setTimeout(() => {
                alertDiv.remove();
            }, 300);
        }, 3000);
    }
    
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-20px); }
        }
    `;
    document.head.appendChild(style);
    
    const prevPageBtn = document.querySelector('.prev-page');
    const nextPageBtn = document.querySelector('.next-page');
    const pageBtns = document.querySelectorAll('.page-btn');
    
    let currentPage = 1;
    const rowsPerPage = 5;
    
    if (prevPageBtn && nextPageBtn && pageBtns) {
        updateTable();
        
        prevPageBtn.addEventListener('click', function() {
            if (currentPage > 1) {
                currentPage--;
                updateTable();
            }
        });
        
        nextPageBtn.addEventListener('click', function() {
            const totalRows = suppliersTable.querySelectorAll('tbody tr:not([style*="display: none"])').length;
            if (currentPage < Math.ceil(totalRows / rowsPerPage)) {
                currentPage++;
                updateTable();
            }
        });
        
        pageBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                currentPage = parseInt(this.getAttribute('data-page'));
                updateTable();
            });
        });
    }
    
    function updateTable() {
        const rows = Array.from(suppliersTable.querySelectorAll('tbody tr:not([style*="display: none"])'));
        const totalRows = rows.length;
        const totalPages = Math.ceil(totalRows / rowsPerPage);
        
        rows.forEach(row => {
            row.style.display = 'none';
        });
        
        const start = (currentPage - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        
        for (let i = start; i < end && i < totalRows; i++) {
            rows[i].style.display = '';
        }
        
        document.getElementById('startItem').textContent = start + 1;
        document.getElementById('endItem').textContent = Math.min(end, totalRows);
        document.getElementById('totalItems').textContent = totalRows;
        
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages;
        
        pageBtns.forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline');
            
            if (parseInt(btn.getAttribute('data-page')) === currentPage) {
                btn.classList.remove('btn-outline');
                btn.classList.add('btn-primary');
            }
        });
    }
});
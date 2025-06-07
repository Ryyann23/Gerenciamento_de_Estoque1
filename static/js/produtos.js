let currentProductId = null;
const itemsPerPage = 5;
let currentPage = 1;
let filteredProducts = [];

const modal = document.getElementById('productModal');
const modalTitle = document.getElementById('modalTitle');
const productForm = document.getElementById('productForm');
const productIdInput = document.getElementById('productId');
const productNameInput = document.getElementById('productName');
const productCategoryInput = document.getElementById('productCategory');
const productPriceInput = document.getElementById('productPrice');
const productStockInput = document.getElementById('productStock');
const closeModalButtons = document.querySelectorAll('.close-modal');
const addProductBtn = document.getElementById('addProductBtn');
const searchInput = document.getElementById('searchInput');
const categoryFilter = document.getElementById('categoryFilter');
const statusFilter = document.getElementById('statusFilter');
const applyFiltersBtn = document.getElementById('applyFilters');
const prevPageBtn = document.querySelector('.prev-page');
const nextPageBtn = document.querySelector('.next-page');
const pageBtns = document.querySelectorAll('.page-btn');
const startItemSpan = document.getElementById('startItem');
const endItemSpan = document.getElementById('endItem');
const totalItemsSpan = document.getElementById('totalItems');
let allProductRows = Array.from(document.querySelectorAll('#productsTable tbody tr'));

function removerAcentos(texto) {
    return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

filteredProducts = allProductRows;
updatePagination();

function updatePagination() {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, filteredProducts.length);
    
    allProductRows.forEach(row => row.style.display = 'none');
    
    filteredProducts.slice(startIndex, endIndex).forEach(row => {
        row.style.display = '';
    });
    
    startItemSpan.textContent = startIndex + 1;
    endItemSpan.textContent = endIndex;
    totalItemsSpan.textContent = filteredProducts.length;
    
    prevPageBtn.disabled = currentPage === 1;
    nextPageBtn.disabled = endIndex >= filteredProducts.length;
    
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    updatePageButtons(totalPages);
}

function updatePageButtons(totalPages) {
    const paginationControls = document.querySelector('.pagination-controls');
    paginationControls.innerHTML = '';
    
    const prevBtn = document.createElement('button');
    prevBtn.className = 'btn btn-outline prev-page';
    prevBtn.style.padding = '8px 12px';
    prevBtn.disabled = currentPage === 1;
    prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            updatePagination();
        }
    });
    paginationControls.appendChild(prevBtn);
    
    for (let i = 1; i <= totalPages; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.className = `btn ${i === currentPage ? 'btn-primary' : 'btn-outline'} page-btn`;
        pageBtn.style.padding = '8px 12px';
        pageBtn.textContent = i;
        pageBtn.dataset.page = i;
        pageBtn.addEventListener('click', () => {
            currentPage = i;
            updatePagination();
        });
        paginationControls.appendChild(pageBtn);
    }
    
    const nextBtn = document.createElement('button');
    nextBtn.className = 'btn btn-outline next-page';
    nextBtn.style.padding = '8px 12px';
    nextBtn.disabled = currentPage * itemsPerPage >= filteredProducts.length;
    nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
    nextBtn.addEventListener('click', () => {
        if (currentPage * itemsPerPage < filteredProducts.length) {
            currentPage++;
            updatePagination();
        }
    });
    paginationControls.appendChild(nextBtn);
}

function filterProducts() {
    const category = categoryFilter.value.toLowerCase();
    const status = statusFilter.value.toLowerCase();
    const searchTerm = searchInput.value.toLowerCase();
    
    filteredProducts = allProductRows.filter(row => {
        const rowCategory = row.cells[2].textContent.toLowerCase();
        const rowStatus = row.querySelector('.status-badge').textContent.toLowerCase();
        const rowText = removerAcentos(row.textContent.toLowerCase());
        const searchTermNoAccents = removerAcentos(searchTerm);
        
        const categoryMatch = !category || rowCategory.includes(category);
        const statusMatch = !status || rowStatus.includes(status);
        const searchMatch = !searchTerm || rowText.includes(searchTermNoAccents);
        
        return categoryMatch && statusMatch && searchMatch;
    });
    
    currentPage = 1;
    updatePagination();
}

addProductBtn.addEventListener('click', () => {
    currentProductId = null;
    modalTitle.textContent = 'Adicionar Novo Produto';
    productForm.reset();
    productIdInput.value = '';
    modal.style.display = 'flex';
});

document.querySelectorAll('.edit-btn').forEach(button => {
    button.addEventListener('click', function() {
        const productId = this.getAttribute('data-id');
        const productRow = document.querySelector(`tr[data-id="${productId}"]`);
        
        if (productRow) {
            currentProductId = productId;
            modalTitle.textContent = 'Editar Produto';
            
            productIdInput.value = productId;
            productNameInput.value = productRow.querySelector('div[style="font-weight: 500;"]').textContent;
            productCategoryInput.value = productRow.cells[2].textContent;
            productPriceInput.value = productRow.cells[4].textContent.replace('R$ ', '').trim();
            productStockInput.value = productRow.cells[3].textContent;
            
            modal.style.display = 'flex';
        }
    });
});

closeModalButtons.forEach(button => {
    button.addEventListener('click', () => {
        modal.style.display = 'none';
    });
});

window.addEventListener('click', (event) => {
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

applyFiltersBtn.addEventListener('click', filterProducts);
searchInput.addEventListener('input', filterProducts);

document.querySelectorAll('.delete-btn').forEach(button => {
    button.addEventListener('click', async function() {
        const productId = this.getAttribute('data-id');
        
        if (confirm('Tem certeza que deseja excluir este produto?')) {
            try {
                const response = await fetch('/delete_product', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ id: productId })
                });
                
                if (response.ok) {
                    const result = await response.json();
                    if (result.success) {
                        window.location.reload();
                    } else {
                        alert('Erro: ' + (result.message || 'Falha ao excluir o produto'));
                    }
                } else {
                    throw new Error('Erro na requisição');
                }
            } catch (error) {
                console.error('Erro:', error);
                alert('Erro ao excluir o produto. Tente novamente.');
            }
        }
    });
});

productForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const productData = {
        name: productNameInput.value,
        category: productCategoryInput.value,
        price: parseFloat(productPriceInput.value),
        stock: parseInt(productStockInput.value),
        action: currentProductId ? 'update' : 'create'
    };
    
    if (currentProductId) {
        productData.id = currentProductId;
    }
    
    try {
        const response = await fetch(currentProductId ? '/update_product' : '/add_product', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(productData)
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                window.location.reload();
            } else {
                alert('Erro: ' + (result.message || 'Falha ao salvar o produto'));
            }
        } else {
            throw new Error('Erro na requisição');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao salvar o produto. Tente novamente.');
    }
});
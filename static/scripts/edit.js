document.addEventListener('DOMContentLoaded', () => {
    const BASE_URL = window.APP_CONFIG?.BASE_URL || "http://127.0.0.1:5001";
    const containerId = new URLSearchParams(window.location.search).get('container_id');
    const elements = {
        appContainer: document.getElementById('app'),
        clearButton: document.getElementById('clearButton'),
        errorMessage: document.getElementById('error-message'),
        errorSound: document.getElementById('error-sound'),
        successSound: document.getElementById('success-sound'),
        articleFilter: document.getElementById('article-filter'),
        dmInput: document.getElementById('dm-input'),
        confirmationModal: document.getElementById('confirmation-modal'),
        modalDmInfo: document.getElementById('modal-dm-info'),
        confirmDeleteBtn: document.getElementById('confirm-delete-btn'),
        cancelDeleteBtn: document.getElementById('cancel-delete-btn'),
        containerNameHeader: document.getElementById('container-name-header'),
		toShipmentsButton : document.getElementById('shipmentButton'),
		toMainMenuButton : document.getElementById('mainMenuButton'),
    };

    // Проверка наличия всех элементов
    if (Object.values(elements).includes(null)) {
        console.error('One or more required elements are missing in the DOM');
        return;
    }

    let containerKitData = [];
    let currentDmToDelete = null;

    // Инициализация контейнера, если containerId существует
    if (!containerId) {
        elements.appContainer.innerHTML = '<div class="error">Error: container_id not specified in URL.</div>';
    } else {
        fetchContainerKit();
        addEventListeners();
    }

    function addEventListeners() {
        elements.clearButton.addEventListener('click', clearInput);
        elements.articleFilter.addEventListener('change', applyFilters);
        elements.dmInput.addEventListener('input', checkDmCode);
        elements.confirmDeleteBtn.addEventListener('click', confirmDeletion);
        elements.cancelDeleteBtn.addEventListener('click', cancelDeletion);
		elements.toShipmentsButton.addEventListener('click', goToKit);
		elements.toMainMenuButton.addEventListener('click', goToMain);
    }

    async function fetchContainerKit() {
        elements.appContainer.innerHTML = '<div class="loading">Loading...</div>';
        const accessToken = localStorage.getItem('access_token');
        try {
            const response = await fetch(`${BASE_URL}/api/containers/kit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`,
                },
                body: JSON.stringify({ container_id: parseInt(containerId) })
            });

            if (response.status === 401) {
                await refreshAccessToken();
                return fetchContainerKit();  // Retry the request
            }

            if (!response.ok) throw new Error('Error fetching data');
            const data = await response.json();

            if (data.success) {
                containerKitData = data.container_kit.scanned;
                displayContainerName(data.container_kit.container_name);
                populateArticleFilter();
                displayContainerKit(containerKitData);
            } else {
                throw new Error('Unable to fetch container kit');
            }
        } catch (err) {
            elements.appContainer.innerHTML = `<div class="error">Error: ${err.message}</div>`;
        }
    }

	function displayContainerName(containerName) {
		elements.containerNameHeader.innerHTML = `
			<div class="container-name-section">
				<span id="container-name-text">${escapeHtml(containerName)}</span>
				<button id="edit-name-btn">Edit Name</button>
			</div>
		`;
		
		document.getElementById('edit-name-btn').addEventListener('click', () => {
			showEditContainerName(containerName);
		});
	}

    function showEditContainerName(currentName) {
        elements.containerNameHeader.innerHTML = `
            <input type="text" id="edit-container-name-input" value="${escapeHtml(currentName)}" />
            <button id="save-name-btn">Save</button>
            <button id="cancel-edit-btn">Cancel</button>
        `;

        document.getElementById('save-name-btn').addEventListener('click', saveContainerName);
        document.getElementById('cancel-edit-btn').addEventListener('click', () => {
            displayContainerName(currentName);
        });
    }

    async function saveContainerName() {
		const accessToken = localStorage.getItem('access_token');  // Retrieve the access token from localStorage
        const newContainerName = document.getElementById('edit-container-name-input').value;
        try {
            const response = await fetch(`${BASE_URL}/api/containers/rename`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`  // Add Authorization header
                },
                body: JSON.stringify({ container_id: parseInt(containerId), new_container_name: newContainerName })
            });

            const data = await response.json();
            if (data.success) {
                displayContainerName(newContainerName);
                playSuccessSound();
            } else {
                throw new Error(data.message || 'Failed to rename container');
            }
        } catch (err) {
            showError(`Error: ${err.message}`);
        }
    }

    function populateArticleFilter() {
        const articles = new Set(containerKitData.map(item => item.article));
        updateDropdown(elements.articleFilter, Array.from(articles));
    }

    function updateDropdown(dropdown, values) {
        dropdown.innerHTML = '<option value="">All</option>';
        values.forEach(value => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = value;
            dropdown.appendChild(option);
        });
    }

    function applyFilters() {
        const selectedArticle = elements.articleFilter.value;
        const filteredData = containerKitData.filter(item =>
            !selectedArticle || item.article === selectedArticle
        );
        displayContainerKit(filteredData);
    }

    function displayContainerKit(filteredKit) {
        if (!filteredKit.length) {
            elements.appContainer.innerHTML = '<div class="error">No matching results found.</div>';
            return;
        }

        const html = `
            <h1>Container Kit</h1>
            <table>
                <thead>
                    <tr><th>Article</th><th>Invoice ID</th><th>Number</th><th>Actions</th></tr>
                </thead>
                <tbody>
                    ${filteredKit.flatMap(item => item.dms.map(dm => `
                        <tr>
                            <td>${escapeHtml(item.article)}</td>
                            <td>${escapeHtml(dm.invoice_date)}</td>
                            <td>${escapeHtml(dm.current_page_num)}</td>
                            <td>
                                <button class="delete-btn" 
                                        data-dm="${encodeURIComponent(dm.dm_without_tail)}" 
                                        data-invoice-date="${encodeURIComponent(dm.invoice_date)}" 
                                        data-page-num="${encodeURIComponent(dm.current_page_num)}">
                                    🗑️
                                </button>
                            </td>
                        </tr>
                    `)).join('')}
                </tbody>
            </table>
        `;

        elements.appContainer.innerHTML = html;
        attachDeleteListeners();
    }

    function attachDeleteListeners() {
        document.querySelectorAll('.delete-btn').forEach(button => {
            button.addEventListener('click', (event) => {
                const dm = decodeURIComponent(event.target.dataset.dm);
                const invoiceDate = decodeURIComponent(event.target.dataset.invoiceDate);
                const pageNum = decodeURIComponent(event.target.dataset.pageNum);
                showDeleteConfirmation(dm, invoiceDate, pageNum);
            });
        });
    }

    function showDeleteConfirmation(dmWithoutTail, invoiceDate, currentPageNum) {
        elements.modalDmInfo.textContent = `
            Matching DM code found:\n\n
            DM Without Tail: ${dmWithoutTail}\n
            Invoice ID: ${invoiceDate}\n
            Number: ${currentPageNum}
        `;
        currentDmToDelete = { dmWithoutTail, invoiceDate, currentPageNum };
        elements.confirmationModal.classList.add('show'); 
    }

    function checkDmCode() {
        const inputValue = elements.dmInput.value.substring(0, 31); // Limit to 31 chars
        if (elements.dmInput.value.length < 85 || !elements.dmInput.value.startsWith("0104")) return;

        const matchingItem = containerKitData.flatMap(item => item.dms)
            .find(dm => dm.dm_without_tail.startsWith(inputValue));

        if (matchingItem) {
            showDeleteConfirmation(matchingItem.dm_without_tail, matchingItem.invoice_date, matchingItem.current_page_num);
            elements.dmInput.value = '';
        }
    }

    async function confirmDeletion() {
        if (!currentDmToDelete) return;

        try {
            await deleteDmCode(currentDmToDelete.dmWithoutTail);
            elements.confirmationModal.classList.remove('show');
        } catch (err) {
            console.error('Failed to delete DM code:', err);
            showError('Failed to delete DM code');
        }
    }
	
	async function goToKit() {
         window.location.href = `/containers/kit.html?container_id=${containerId}`;
        
    }
	async function goToMain() {
         window.location.href = `/containers/container.html`;
        
    }

    async function cancelDeletion() {
        elements.confirmationModal.classList.remove('show');
        currentDmToDelete = null;
    }

function checkAndPromptDeleteContainer() {
    if (containerKitData.length === 0) {
        const confirmation = confirm("This container is empty. Delete this?");
        if (confirmation) {
            deleteContainer();
        }
    }
}

	async function deleteContainer() {
		const accessToken = localStorage.getItem('access_token');
		try {
			const response = await fetch(`${BASE_URL}/api/containers/delete`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${accessToken}`,
				},
				body: JSON.stringify({ container_id: parseInt(containerId) })
			});

			if (response.status === 401) {
				await refreshAccessToken();
				return deleteContainer(); // Retry after refreshing token
			}

			if (!response.ok) throw new Error('Error deleting container');

			const data = await response.json();
			if (data.success) {
				alert("Container deleted successfully.");
				window.location.href = '/containers/container.html'; // Redirect to main container page
			} else {
				throw new Error(data.message || 'Failed to delete container');
			}
		} catch (err) {
			showError(`Error: ${err.message}`);
		}
	}

	// Modify deleteDmCode to check container state after deletion
	async function deleteDmCode(dmWithoutTail) {
		const accessToken = localStorage.getItem('access_token');
		try {
			const response = await fetch(`${BASE_URL}/api/dm/delete`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${accessToken}`,
				},
				body: JSON.stringify({ dm_without_tail: dmWithoutTail, container_id: parseInt(containerId) })
			});

			if (response.status === 401) {
				await refreshAccessToken();
				return deleteDmCode(dmWithoutTail); // Retry the request
			}

			if (!response.ok) throw new Error('Error deleting DM code');

			const data = await response.json();
			if (data.success) {
				playSuccessSound();
				await fetchContainerKit();
				checkAndPromptDeleteContainer(); // Check if container is empty after deletion
			} else {
				throw new Error(data.message || 'Failed to delete DM code');
			}
		} catch (err) {
			showError(`Error: ${err.message}`);
		}
	}

	
	async function refreshAccessToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            alert('No refresh token available');
            return;
        }

        try {
            const response = await fetch(`${BASE_URL}/api/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            const data = await response.json();
            if (data.access_token) {
                localStorage.setItem('access_token', data.access_token);
            } else {
                alert('Failed to refresh the access token');
            }
        } catch (error) {
            console.error('Error refreshing access token:', error);
            alert('Error refreshing access token');
        }
    }


    function showError(message) {
        elements.errorMessage.textContent = message;
        elements.errorSound.play();
    }

    function clearInput() {
        elements.articleFilter.value = '';
        fetchContainerKit();
    }

    function playSuccessSound() {
        elements.successSound.play();
    }

    function escapeHtml(text) {
        if (typeof text !== 'string') return text;
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;',
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
});

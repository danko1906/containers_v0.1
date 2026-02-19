
const BASE_URL = window.APP_CONFIG?.BASE_URL || "http://127.0.0.1:5001";

document.addEventListener('DOMContentLoaded', () => {
    const createButton = document.getElementById('createButton');
    const containerNameInput = document.getElementById('containerName');
    const containersDropdown = document.getElementById('containersDropdown');
    const goToShipmentButton = document.getElementById('goToShipmentButton');
    const editButton = document.getElementById('editButton');
    const deleteButton = document.getElementById('deleteButton');
    const downloadButton = document.getElementById('downloadButton');
	const errorSound = document.getElementById('error-sound');
	const successSound = document.getElementById('success-sound');

    let selectedContainerId = null;
    let selectedContainerStatus = null;

    // Store container data in memory to prevent repeated API calls
    let cachedContainers = null;

	function formatPackedDate(packedDate) {
		return packedDate || 'N/A';
	}

	function buildContainerMeta(container) {
		return `container_id: ${container.container_id ?? 'N/A'} | packed_date: ${formatPackedDate(container.packed_date)} | created_by_id: ${container.created_by_id ?? 'N/A'}`;
	}

	function createContainerOption(container) {
		const option = document.createElement('option');
		option.value = String(container.container_id);
		option.textContent = container.container_name || `Container ${container.container_id}`;
		//const containerName = container.container_name || `Container ${container.container_id}`;
		//const containerMeta = buildContainerMeta(container);
		//option.textContent = `${containerName} \u2003\u2003 | ${containerMeta}`;
		option.dataset.containerName = container.container_name || `Container ${container.container_id}`;
		option.dataset.containerMeta = buildContainerMeta(container);
		option.dataset.containerId = container.container_id ?? '';
		option.dataset.packedDate = container.packed_date ?? '';
		option.dataset.createdById = container.created_by_id ?? '';
		return option;
	}
	
	function playErrorSound() {
	   errorSound.play();
	}

	function playSuccessSound() {
	   successSound.play();
	}
    // Fetch and display existing containers
    async function loadContainers() {
		let container_statuses=getContainerStatuses()
        let accessToken = localStorage.getItem('access_token');
        if (!accessToken) {
            alert('No access token available');
            return;
        }
		
        try {
            const response = await fetch(`${BASE_URL}/api/containers/get`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`  // Add Authorization header
                },
                body: JSON.stringify({ container_statuses })  // Send container_statuses in the request body
            });

            if (response.status === 401) {
                // Token expired, refresh the token
                await refreshAccessToken();
                loadContainers();  // Retry loading containers after refreshing token
                return;
            }

            const data = await response.json();

            if (data.success && data.containers.success) {
                cachedContainers = data.containers.containers;
                updateContainersDropdown(cachedContainers);
            } else {
                alert('Error loading containers');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error fetching containers');
        }
    }

    function updateContainersDropdown(containers) {
        containersDropdown.innerHTML = '<option value="">-- Select a Container --</option>';
        containers.forEach(container => {
            const option = createContainerOption(container);
            containersDropdown.appendChild(option);
        });
    }

    // Refresh the access token using the refresh token
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
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });

            const data = await response.json();
            if (data.access_token) {
                // Save the new access token
                localStorage.setItem('access_token', data.access_token);
            } else {
                alert('Failed to refresh the access token');
            }
        } catch (error) {
            console.error('Error refreshing access token:', error);
            alert('Error refreshing access token');
        }
    }
	function updateDmInfoPanel(dmInfo) {
		document.getElementById('dmArticle').textContent = dmInfo.article || 'N/A';
		document.getElementById('dmInvoiceDate').textContent = dmInfo.invoice_date || 'N/A';
		document.getElementById('dmCurrentPageNum').textContent = dmInfo.current_page_num || 'N/A';
		document.getElementById('dmStatus').textContent = dmInfo.status || 'N/A';
		
		if (dmInfo.status === 'packed' && dmInfo.container_info) {
			document.getElementById('dmContainerName').textContent = dmInfo.container_info.container_name || 'N/A';
			document.getElementById('dmContainerStatus').textContent = dmInfo.container_info.container_status || 'N/A';
			document.getElementById('dmPackedDate').textContent = dmInfo.container_info.packed_date || 'Not packed yet';
		} else {
			document.getElementById('dmContainerName').textContent = '-';
			document.getElementById('dmContainerStatus').textContent = '-';
			document.getElementById('dmPackedDate').textContent = '-';
		}

		document.getElementById('dmInfoPanel').style.display = 'block'; // Показываем панель
	}

	async function handleDmInfoInput() {
		const accessToken = localStorage.getItem('access_token');
		const input = dmInput.value.trim();

		if (input.length !== 85 || !input.startsWith("0104")) {
			showWarning(`The string must be 85 characters long and start with '0104'.`);
			return;
		}

		const dm_without_tail = input.slice(0, 31);

		try {
			const response = await fetch(`${BASE_URL}/api/dm/info`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${accessToken}`
				},
				body: JSON.stringify({ dm_without_tail })
			});

			if (response.status === 401) {
				await refreshAccessToken();
				handleDmInfoInput();
				return;
			}

			const data = await response.json();
			if (data.success && data.data) {
				updateDmInfoPanel(data.data);
				playSuccessSound();
				dmInput.value = '';
			} else {
				showErrorMessage('Failed to retrieve DM info.');
			}
		} catch (error) {
			console.error('Error fetching DM info:', error);
			playErrorSound();
			showErrorMessage('Error fetching DM info.');
		}
	}

    function showSuccessMessage(message) {
        messageBox.style.color = 'green';
        messageBox.textContent = message;
    }

    function showErrorMessage(message) {
        messageBox.style.color = 'red';
        messageBox.textContent = message;
    }

	dmInput.addEventListener('input', (e) => {


		if (e.target.value.length === 85) {
			handleDmInfoInput(); // Автоматически вызываем функцию при 85 символах
		}
	});
    // Handle container selection
    containersDropdown.addEventListener('change', (e) => {
        selectedContainerId = e.target.value;
        const isSelected = !!selectedContainerId;
        goToShipmentButton.disabled = !isSelected;

        if (selectedContainerId) {
            const selectedContainer = cachedContainers.find(container => container.container_id == selectedContainerId);

            if (selectedContainer) {
                selectedContainerStatus = selectedContainer.container_status;
                if (selectedContainerStatus === 'new') {
                    editButton.style.display = 'none';
                    editButton.disabled = true;  
                    deleteButton.style.display = 'inline-block';
                } else if (selectedContainerStatus === 'packing') {
                    editButton.style.display = 'inline-block';
                    editButton.disabled = false;
                    deleteButton.style.display = 'none';
                } else {
                    editButton.style.display = 'none';
                    editButton.disabled = true;  
                    deleteButton.style.display = 'none';
                }
            } else {
                alert('Container not found');
            }
        } else {
            editButton.style.display = 'none';
            editButton.disabled = true;  
            deleteButton.style.display = 'none';
        }
    });

    // Handle Go to Shipments button click
    goToShipmentButton.addEventListener('click', () => {
        if (selectedContainerId) {
            window.location.href = `kit.html?container_id=${selectedContainerId}`;
        } else {
            alert('Please select a container to proceed to shipments');
        }
    });

    // Handle Edit button click
    editButton.addEventListener('click', () => {
        if (selectedContainerId) {
            window.location.href = `edit.html?container_id=${selectedContainerId}`;
        } else {
            alert('Please select a container to edit');
        }
    });

    // Handle Delete button click
    deleteButton.addEventListener('click', () => {
        const confirmDelete = confirm('Are you sure you want to delete this container?');
        if (confirmDelete) {
            deleteContainer();
        }
    });

    async function deleteContainer() {
        if (!selectedContainerId) return;

        const accessToken = localStorage.getItem('access_token');  // Retrieve the access token from localStorage

        try {
            const response = await fetch(`${BASE_URL}/api/containers/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`  // Add Authorization header
                },
                body: JSON.stringify({ container_id: selectedContainerId }),
            });

            if (response.status === 401) {
                // Token expired, refresh the token
                await refreshAccessToken();
                deleteContainer();  // Retry after refreshing token
                return;
            }

            const result = await response.json();
            if (result.success) {
                alert('Container deleted successfully');
                loadContainers();  // Reload containers after deletion
            } else {
                alert(`Error: ${result.message}`);
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }

	async function createContainer() {
		const containerName = containerNameInput.value.trim();
		const accessToken = localStorage.getItem('access_token');
		
		if (!containerName) {
			alert('Please enter a container name');
			return;
		}

		try {
			const response = await fetch(`${BASE_URL}/api/containers/create`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${accessToken}`
				},
				body: JSON.stringify({ container_name: containerName }),
			});

			if (response.status === 401) {
				await refreshAccessToken();
				createContainer();  // Retry after refreshing token
				return;
			}

			const result = await response.json();

			if (result.success && result.container_id) {
				window.location.href = `/containers/kit.html?container_id=${result.container_id}`;
			} else {
				alert(`Error: ${result.message}`);
			}
		} catch (error) {
			console.error('Error:', error);
			alert('Failed to create container');
		}
	}

	createButton.addEventListener('click', createContainer);
	
	
// Add a "Show packed" checkbox
	const showPackedCheckbox = document.getElementById('showPackedCheckbox'); // Assuming the checkbox has this id
	showPackedCheckbox.addEventListener('change', () => {
		loadContainers();
		updateButtons();// Reload containers based on the new status filter
	});

	// Update container status handling and button logic
	containersDropdown.addEventListener('change', updateButtons);
	function updateButtons() {
		selectedContainerId = containersDropdown.value;
		const isSelected = !!selectedContainerId;
		goToShipmentButton.disabled = !isSelected;

		if (selectedContainerId) {
			const selectedContainer = cachedContainers.find(container => container.container_id == selectedContainerId);

			if (selectedContainer) {
				selectedContainerStatus = selectedContainer.container_status;

				if (selectedContainerStatus === 'new') {
					editButton.style.display = 'none';
					goToShipmentButton.style.display = 'inline-block';
					goToShipmentButton.disabled = false;
					editButton.disabled = true;
					downloadButton.disabled = true;
					downloadButton.style.display = 'none'; 
					deleteButton.style.display = 'inline-block';
				} else if (selectedContainerStatus === 'packing') {
					goToShipmentButton.style.display = 'inline-block';
					goToShipmentButton.disabled = false;
					editButton.style.display = 'inline-block';
					editButton.disabled = false;
					downloadButton.disabled = true;
					downloadButton.style.display = 'none'; 
					deleteButton.style.display = 'none';
				} else if (selectedContainerStatus === 'packed') {
					editButton.style.display = 'none';
					editButton.disabled = true;
					goToShipmentButton.style.display = 'none';
					goToShipmentButton.disabled = true;
					deleteButton.style.display = 'none';
					downloadButton.disabled = false;
					downloadButton.style.display = 'inline-block';
				} else {
					editButton.style.display = 'none';
					editButton.disabled = true;
					deleteButton.style.display = 'none';
				}
			} else {
				alert('Container not found');
			}
		} else {
			editButton.style.display = 'none';
			editButton.disabled = true;
			deleteButton.style.display = 'none';
		}
	}

	function getContainerStatuses() {
	  const showPackedCheckbox = document.getElementById('showPackedCheckbox');
	  
	  // Проверяем состояние чекбокса
	  if (showPackedCheckbox && !showPackedCheckbox.checked) {
		return ["new", "packing"];
	  } else {
		return ["packed"];
	  }
	}

	async function downloadContainersBulk(containerIds) {
		const accessToken = localStorage.getItem('access_token');
		if (!accessToken) {
			alert('No access token available');
			return;
		}

		const body = {
			container_ids: containerIds,
			order_by: 'container_id',
			order_dir: 'desc'
		};

		try {
			const response = await fetch(`${BASE_URL}/api/containers/download_bulk`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${accessToken}`
				},
				credentials: 'include',
				body: JSON.stringify(body)
			});

			if (response.status === 401) {
				await refreshAccessToken();
				return downloadContainersBulk(containerIds);
			}

			if (!response.ok) {
				throw new Error(await response.text());
			}

			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = 'containers_bulk.xlsx';
			document.body.appendChild(a);
			a.click();
			a.remove();
			window.URL.revokeObjectURL(url);
		} catch (error) {
			console.error('Bulk download error:', error);
			alert(`Failed to download containers list: ${error.message}`);
		}
	}

	// Handle Download button click
	downloadButton.addEventListener('click', async () => {
		const packedContainerIds = [...new Set(
			(cachedContainers || [])
				.filter(container => container.container_status === 'packed')
				.map(container => Number(container.container_id))
				.filter(Number.isFinite)
		)];

		if (!packedContainerIds.length && selectedContainerId) {
			packedContainerIds.push(Number(selectedContainerId));
		}

		if (!packedContainerIds.length) {
			alert('No packed containers available for bulk download');
			return;
		}

		await downloadContainersBulk(packedContainerIds);
	});



    // Initial load of containers
    loadContainers();
});

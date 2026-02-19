const BASE_URL = window.APP_CONFIG?.BASE_URL || "http://127.0.0.1:5001";
const containerId = new URLSearchParams(window.location.search).get('container_id');
const appContainer = document.getElementById('app');
const dmInput = document.getElementById('dmInput');
const clearButton = document.getElementById('clearButton');
const errorMessage = document.getElementById('error-message');
const errorSound = document.getElementById('error-sound');
const successSound = document.getElementById('success-sound');
const modeSwitch = document.getElementById('modeSwitch');
const modeText = document.getElementById('modeText');
const modalText = document.getElementById('modalText');
const confirmationModal = document.getElementById('confirmationModal');
const modalModeText = document.getElementById('modalMode');
const confirmButton = document.getElementById('confirmButton'); // Было confirmSwitchButton
const cancelButton = document.getElementById('cancelButton');  


modeSwitch.addEventListener('change', () => {
    showConfirmationModal(
        `Are you sure you want to switch to ${containerApp.currentMode === 'ADD' ? 'DELETE' : 'ADD'} mode?`,
        'switchMode'
    );
});


	// Изменение обработчика кнопки "Packed"
	document.getElementById('packedButton')?.addEventListener('click', () => {
		showConfirmationModal("Are you sure you want to mark this container as 'Packed'?", 'markPacked', confirmMarkAsPacked);
	});

// Обработчик подтверждения смены режима


class ContainerApp {
  constructor(containerId) {
    this.containerId = containerId;
    this.currentMode = 'ADD';
  }

  init() {
    if (!this.containerId) {
      appContainer.innerHTML = '<div class="error">Error: container_id not specified in URL.</div>';
      return;
    }

    document.addEventListener('DOMContentLoaded', () => {
      this.fetchContainerKit();
      this.setupEventListeners();
    });
  }

  setupEventListeners() {
    dmInput.addEventListener('input', this.handleDmInput.bind(this));
    clearButton.addEventListener('click', this.clearInput.bind(this));
	document.addEventListener('click', (event) => {
    const ignoredElements = ['BUTTON', 'INPUT', 'LABEL']; // Исключаем кнопки, поля ввода и метки
    if (!ignoredElements.includes(event.target.tagName) && event.target !== modeSwitch) {
        dmInput.focus();
    }
});

  }

	

  async fetchContainerKit() {
	  appContainer.innerHTML = '<div class="loading">Loading...</div>';
	  const accessToken = localStorage.getItem('access_token');

	  try {
		const response = await fetch(`${BASE_URL}/api/containers/kit`, {
		  method: 'POST',
		  headers: {
			'Content-Type': 'application/json',
			'Authorization': `Bearer ${accessToken}`,
		  },
		  body: JSON.stringify({ container_id: parseInt(this.containerId) }),
		});

		if (response.status === 401) {
		  await this.refreshAccessToken();
		  return this.fetchContainerKit();
		}
	
		if (!response.ok) throw new Error('Error fetching data');

		const data = await response.json();
		if (data.success) {
		  this.displayContainerKit(data.container_kit);
		  dmInput.value = '';
		  dmInput.focus();
		} else {
		  throw new Error(data.message || 'Unable to fetch container kit');
		}
	  } catch (err) {
		// Показываем окно ошибки с сообщением
		showErrorPopup(`Error: ${err.message}`);
	  }
	}

	async markAsPacked() {
		showConfirmationModal(
			"Are you sure you want to mark this container as 'Packed'?", 
			'markPacked',
			async () => {
				const accessToken = localStorage.getItem('access_token');
				try {
					const response = await fetch(`${BASE_URL}/api/containers/packed`, {
						method: 'POST',
						headers: {
							'Content-Type': 'application/json',
							'Authorization': `Bearer ${accessToken}`,
						},
						body: JSON.stringify({ container_id: parseInt(this.containerId) }),
					});

					if (response.status === 401) {
						await this.refreshAccessToken();
						return this.markAsPacked();
					}

					if (!response.ok) throw new Error('Failed to mark container as packed');

					const data = await response.json();
					if (data.success) {
						alert('Container successfully marked as "Packed".');
						appContainer.innerHTML = `<p>Container is packed!</p>`;
						window.location.href = `/containers/download.html?container_id=${containerId}`;
					} else {
						throw new Error(data.message || 'Error changing container status');
					}
				} catch (err) {
					showErrorPopup(`Error: ${err.message}`);
				}
			}
		);
	}


	  switchMode() {
		this.currentMode = this.currentMode === 'ADD' ? 'DELETE' : 'ADD';
		modeText.textContent = `${this.currentMode} Mode`;

		if (this.currentMode === 'ADD') {
		  document.body.style.backgroundColor = '#BBDEFB';
		  document.querySelectorAll('button').forEach(btn => btn.style.backgroundColor = '#2196F3');
		} else {
		  document.body.style.backgroundColor = '#FFCDD2';
		  document.querySelectorAll('button').forEach(btn => btn.style.backgroundColor = '#F44336');
		}
		
		// Очищаем поле ввода и устанавливаем фокус
		dmInput.value = '';
		dmInput.focus();
	  }

	


	displayContainerKit(containerKit) {
		const containerStatus = containerKit.container_status;

		// Убираем "Loading..." при загрузке данных
		const loadingElement = document.querySelector('.loading');
		if (loadingElement) {
			loadingElement.remove();
		}

		// Создаем контейнер для динамического контента, если он отсутствует
		let containerContent = document.getElementById('containerContent');
		if (!containerContent) {
			containerContent = document.createElement('div');
			containerContent.id = 'containerContent';
			appContainer.appendChild(containerContent);
		}

		// Если кнопки еще нет, создаем её один раз
		let packedButton = document.getElementById('packedButton');
		if (!packedButton) {
			packedButton = document.createElement('button');
			packedButton.id = 'packedButton';
			packedButton.textContent = 'Packed';
			packedButton.addEventListener('click', this.markAsPacked.bind(this));
			appContainer.appendChild(packedButton);
		}

		// Обновляем только контейнер с контентом, не затрагивая кнопку
		let html = `<h1>${containerKit.container_name}</h1>`;

		if (containerStatus === "packing") {
			html += `
				<table>
					<thead>
						<tr><th>Article</th><th>Total</th></tr>
					</thead>
					<tbody>
						${containerKit.scanned.map(item => `
							<tr><td>${item.article}</td><td>${item.total}</td></tr>
						`).join('')}
					</tbody>
				</table>
			`;
		} else if (containerStatus === "new") {
			html += `<p>Just start scan</p>`;
		}

		// Вставляем обновленный контент в контейнер, не трогая кнопку
		containerContent.innerHTML = html;
	}



  async handleDmInput() {
	  const input = dmInput.value.trim();
	  if (input.length !== 85 || !input.startsWith("0104")) {
		showWarning(`The string must be 85 characters long and start with '0104'.`);
		dmInput.value = '';
        dmInput.focus();
		return;
	  }


    errorMessage.textContent = '';
    const dm_without_tail = input.slice(0, 31);
    const accessToken = localStorage.getItem('access_token');
    let endpoint = this.currentMode === 'ADD' ? `${BASE_URL}/api/dm/add` : `${BASE_URL}/api/dm/delete`;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ dm_without_tail: dm_without_tail, container_id: parseInt(this.containerId) }),
      });

      if (response.status === 401) {
        await this.refreshAccessToken();
        return this.handleDmInput();
      }

      if (!response.ok && response.status!=400) throw new Error('Error processing DM code');

      const data = await response.json();
      if (data.success) {
        this.displayContainerKit(data.container_kit);
        this.playSuccessSound();
        dmInput.value = '';
        dmInput.focus();
      } else {
        throw new Error(data.message || 'Failed to process DM code');
      }
    } catch (err) {
	  this.playErrorSound();
	  dmInput.value = '';
      dmInput.focus();
      showErrorPopup(`Error: ${err.message}`);

    } finally {
      dmInput.focus();
    }
  }



  clearInput() {
    dmInput.value = '';
    dmInput.focus();
  }

  playErrorSound() {
   errorSound.play();
  }
  playSuccessSound() {
    successSound.play();
  }

  async refreshAccessToken() {
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
        body: JSON.stringify({ refresh_token: refreshToken }),
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




}

const containerApp = new ContainerApp(containerId);
containerApp.init();

	function showConfirmationModal(text, actionType, onConfirm, onCancel) {
		modalText.textContent = text;
		confirmationModal.style.display = 'block';

		confirmButton.onclick = () => {
			confirmationModal.style.display = 'none';
			if (actionType === 'switchMode') {
				containerApp.switchMode();
			} else if (actionType === 'markPacked') {
				onConfirm();
			}
		};

		cancelButton.onclick = () => {
			confirmationModal.style.display = 'none';
			if (actionType === 'switchMode') {
				modeSwitch.checked = containerApp.currentMode === 'DELETE'; // Откат переключателя
			}
			if (onCancel) onCancel();
				dmInput.focus();
		};
	}

	function showWarning(message) {
	  const warningMessage = document.getElementById('warning-message');
	  warningMessage.textContent = message;
	  warningMessage.style.display = 'block';
	  setTimeout(() => warningMessage.style.display = 'none', 5000); // Скрыть через 5 секунд
	}

	// Показывает окно с ошибкой
	function showErrorPopup(message) {
		const errorPopup = document.getElementById('error-popup');
		const errorText = document.getElementById('error-text');

		errorText.textContent = message;
		errorPopup.style.display = 'block';

		// Automatically close the popup after 10 seconds
		setTimeout(() => {
			errorPopup.style.display = 'none';
		}, 5000);

		closeButton.addEventListener('click', () => {
			errorPopup.style.display = 'none';
		});
	}

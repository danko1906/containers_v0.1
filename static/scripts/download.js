const container_statuses = ["packed"];
const BASE_URL = window.APP_CONFIG?.BASE_URL || "http://127.0.0.1:5001";

function formatPackedDate(packedDate) {
    return packedDate || "N/A";
}

function buildContainerMeta(container) {
    return `container_id: ${container.container_id ?? "N/A"} | packed_date: ${formatPackedDate(container.packed_date)} | created_by_id: ${container.created_by_id ?? "N/A"}`;
}

function createContainerOption(container) {
    const option = document.createElement("option");
    option.value = String(container.container_id);
    const containerName = container.container_name || `Container ${container.container_id}`;
    const containerMeta = buildContainerMeta(container);
    option.textContent = `${containerName} \u2003\u2003 | ${containerMeta}`;
    option.dataset.containerName = container.container_name || `Container ${container.container_id}`;
    option.dataset.containerMeta = containerMeta;
    option.dataset.containerId = container.container_id ?? "";
    option.dataset.packedDate = container.packed_date ?? "";
    option.dataset.createdById = container.created_by_id ?? "";
    return option;
}

function getContainerIdFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get("container_id");
}

document.addEventListener("DOMContentLoaded", function () {
    const multiModeCheckbox = document.getElementById("multiModeCheckbox");
    const singleModeSection = document.getElementById("singleModeSection");
    const multiModeSection = document.getElementById("multiModeSection");
    const containerSelect = document.getElementById("containerSelect");
    const table = document.getElementById("containerTable");
    const tableBody = document.getElementById("tableBody");
    const packedDateFromInput = document.getElementById("packedDateFrom");
    const packedDateToInput = document.getElementById("packedDateTo");
    const applyDateFilterButton = document.getElementById("applyDateFilterButton");
    const resetDateFilterButton = document.getElementById("resetDateFilterButton");
    const selectAllContainers = document.getElementById("selectAllContainers");
    const selectedCount = document.getElementById("selectedCount");
    const multiContainerList = document.getElementById("multiContainerList");
    const downloadButton = document.getElementById("downloadButton");

    let allContainers = [];
    let filteredContainers = [];
    let selectedContainerId = getContainerIdFromURL();
    let isMultiMode = false;
    const selectedContainerIds = new Set();

    function updateDownloadButtonState() {
        if (isMultiMode) {
            downloadButton.textContent = "Download Selected Containers";
            downloadButton.disabled = selectedContainerIds.size === 0;
            return;
        }

        downloadButton.textContent = "Download Selected Container";
        downloadButton.disabled = !selectedContainerId;
    }

    function updateSelectAllState() {
        const total = filteredContainers.length;
        const selected = selectedContainerIds.size;

        if (total === 0) {
            selectAllContainers.checked = false;
            selectAllContainers.indeterminate = false;
            selectAllContainers.disabled = true;
            return;
        }

        selectAllContainers.disabled = false;
        selectAllContainers.checked = selected > 0 && selected === total;
        selectAllContainers.indeterminate = selected > 0 && selected < total;
    }

    function updateSelectedCount() {
        selectedCount.textContent = `Selected: ${selectedContainerIds.size}`;
    }

    function parsePackedDate(value) {
        if (!value) {
            return null;
        }
        const normalized = String(value).trim().replace(" ", "T");
        const parsed = new Date(normalized);
        return Number.isNaN(parsed.getTime()) ? null : parsed;
    }

    function applyPackedDateFilter(showValidationError = true) {
        let fromDate = null;
        let toDate = null;

        if (packedDateFromInput.value) {
            fromDate = new Date(`${packedDateFromInput.value}T00:00:00`);
        }

        if (packedDateToInput.value) {
            toDate = new Date(`${packedDateToInput.value}T23:59:59`);
        }

        if (fromDate && toDate && fromDate > toDate) {
            if (showValidationError) {
                alert("Packed date 'from' cannot be later than packed date 'to'.");
            }
            return false;
        }

        filteredContainers = allContainers
            .filter((container) => {
                const packedDate = parsePackedDate(container.packed_date);
                if (!packedDate) {
                    return false;
                }
                if (fromDate && packedDate < fromDate) {
                    return false;
                }
                if (toDate && packedDate > toDate) {
                    return false;
                }
                return true;
            })
            .sort((a, b) => {
                const aDate = parsePackedDate(a.packed_date);
                const bDate = parsePackedDate(b.packed_date);
                if (!aDate && !bDate) {
                    return 0;
                }
                if (!aDate) {
                    return 1;
                }
                if (!bDate) {
                    return -1;
                }
                return aDate.getTime() - bDate.getTime();
            });

        const validIds = new Set(filteredContainers.map((container) => Number(container.container_id)));
        [...selectedContainerIds].forEach((id) => {
            if (!validIds.has(id)) {
                selectedContainerIds.delete(id);
            }
        });

        renderMultiContainerList();
        return true;
    }

    function renderMultiContainerList() {
        multiContainerList.innerHTML = "";

        if (!filteredContainers.length) {
            const empty = document.createElement("div");
            empty.className = "multi-empty";
            empty.textContent = "No packed containers found.";
            multiContainerList.appendChild(empty);
            updateSelectedCount();
            updateSelectAllState();
            updateDownloadButtonState();
            return;
        }

        filteredContainers.forEach((container) => {
            const containerId = Number(container.container_id);

            const item = document.createElement("label");
            item.className = "multi-item";

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.value = String(containerId);
            checkbox.checked = selectedContainerIds.has(containerId);

            checkbox.addEventListener("change", () => {
                if (checkbox.checked) {
                    selectedContainerIds.add(containerId);
                } else {
                    selectedContainerIds.delete(containerId);
                }
                updateSelectedCount();
                updateSelectAllState();
                updateDownloadButtonState();
            });

            const text = document.createElement("span");
            const containerName = container.container_name || `Container ${container.container_id}`;
            text.textContent = `${containerName} | ${buildContainerMeta(container)}`;

            item.appendChild(checkbox);
            item.appendChild(text);
            multiContainerList.appendChild(item);
        });

        updateSelectedCount();
        updateSelectAllState();
        updateDownloadButtonState();
    }

    function setMode(multiEnabled) {
        isMultiMode = multiEnabled;
        singleModeSection.style.display = isMultiMode ? "none" : "block";
        multiModeSection.style.display = isMultiMode ? "block" : "none";
        if (isMultiMode) {
            applyPackedDateFilter(false);
        }
        updateDownloadButtonState();
    }

    async function fetchContainers() {
        const accessToken = localStorage.getItem("access_token");
        try {
            const response = await fetch(`${BASE_URL}/api/containers/get`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`
                },
                body: JSON.stringify({ container_statuses })
            });

            if (response.status === 401) {
                await refreshAccessToken();
                return fetchContainers();
            }

            const data = await response.json();
            if (!(data.success && data.containers.success)) {
                return;
            }

            allContainers = data.containers.containers || [];

            containerSelect.innerHTML = '<option value="" disabled selected>Select a container</option>';
            allContainers.forEach((container) => {
                containerSelect.appendChild(createContainerOption(container));
            });

            applyPackedDateFilter(false);

            if (selectedContainerId) {
                const selectedOption = containerSelect.querySelector(`option[value="${selectedContainerId}"]`);
                if (selectedOption) {
                    containerSelect.value = String(selectedContainerId);
                    await fetchContainerKit(String(selectedContainerId));
                } else {
                    selectedContainerId = null;
                }
            }

            updateDownloadButtonState();
        } catch (error) {
            console.error("Error fetching containers:", error);
        }
    }

    async function fetchContainerKit(containerId) {
        const accessToken = localStorage.getItem("access_token");
        try {
            const response = await fetch(`${BASE_URL}/api/containers/kit`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`
                },
                body: JSON.stringify({ container_id: containerId })
            });

            if (response.status === 401) {
                await refreshAccessToken();
                return fetchContainerKit(containerId);
            }

            const data = await response.json();
            if (!(data.success && data.container_kit.success)) {
                return;
            }

            tableBody.innerHTML = "";
            data.container_kit.scanned.forEach((item) => {
                const row = document.createElement("tr");
                const articleCell = document.createElement("td");
                const totalCell = document.createElement("td");

                articleCell.textContent = item.article;
                totalCell.textContent = item.total;

                row.appendChild(articleCell);
                row.appendChild(totalCell);
                tableBody.appendChild(row);
            });
            table.style.display = "table";
        } catch (error) {
            console.error("Error fetching container kit:", error);
        }
    }

    async function downloadContainerKit(containerId, containerName) {
        const accessToken = localStorage.getItem("access_token");
        try {
            const response = await fetch(`${BASE_URL}/api/containers/download`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`
                },
                body: JSON.stringify({ container_id: containerId })
            });

            if (response.status === 401) {
                await refreshAccessToken();
                return downloadContainerKit(containerId, containerName);
            }

            if (!response.ok) {
                throw new Error(await response.text());
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            a.download = `${containerName}_kit.xlsx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Error downloading container kit:", error);
            alert(`Failed to download container: ${error.message}`);
        }
    }

    async function downloadContainersBulk(containerIds) {
        const accessToken = localStorage.getItem("access_token");
        const requestBody = {
            container_ids: containerIds,
            order_by: "packed_date",
            order_dir: "asc"
        };

        try {
            const response = await fetch(`${BASE_URL}/api/containers/download_bulk`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`
                },
                credentials: "include",
                body: JSON.stringify(requestBody)
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
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            a.download = "containers_bulk.xlsx";
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Error downloading bulk container list:", error);
            alert(`Failed to download containers list: ${error.message}`);
        }
    }

    containerSelect.addEventListener("change", async function () {
        selectedContainerId = containerSelect.value || null;
        if (!selectedContainerId) {
            table.style.display = "none";
            tableBody.innerHTML = "";
            updateDownloadButtonState();
            return;
        }

        await fetchContainerKit(selectedContainerId);
        updateDownloadButtonState();
    });

    multiModeCheckbox.addEventListener("change", function () {
        setMode(multiModeCheckbox.checked);
    });

    selectAllContainers.addEventListener("change", function () {
        if (selectAllContainers.checked) {
            filteredContainers.forEach((container) => selectedContainerIds.add(Number(container.container_id)));
        } else {
            selectedContainerIds.clear();
        }

        renderMultiContainerList();
    });

    applyDateFilterButton.addEventListener("click", async function () {
        if (!applyPackedDateFilter(true)) {
            return;
        }
        await fetchContainers();
    });

    resetDateFilterButton.addEventListener("click", async function () {
        packedDateFromInput.value = "";
        packedDateToInput.value = "";
        await fetchContainers();
    });

    downloadButton.addEventListener("click", async function () {
        if (isMultiMode) {
            if (!selectedContainerIds.size) {
                alert("Select at least one container for bulk download.");
                return;
            }
            await downloadContainersBulk([...selectedContainerIds]);
            return;
        }

        if (!selectedContainerId) {
            alert("Select a container first.");
            return;
        }

        const selectedOption = containerSelect.options[containerSelect.selectedIndex];
        const containerName = selectedOption?.dataset.containerName || selectedOption?.textContent || "container";
        await downloadContainerKit(selectedContainerId, containerName);
    });

    setMode(false);
    fetchContainers();
});

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) {
        alert("No refresh token available");
        return;
    }

    try {
        const response = await fetch(`${BASE_URL}/api/auth/refresh`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        const data = await response.json();
        if (data.access_token) {
            localStorage.setItem("access_token", data.access_token);
        } else {
            alert("Failed to refresh the access token");
        }
    } catch (error) {
        console.error("Error refreshing access token:", error);
        alert("Error refreshing access token");
    }
}

const API_BASE = `${window.location.origin}/api`;

function apiFetch(path, options = {}) {
    return fetch(`${API_BASE}${path}`, {
        credentials: 'include',
        ...options
    });
}

function showTab(tab) {
    if (tab === 'login') {
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');
    } else {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');
    }
}

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const login = document.querySelector('#login-form input[type="text"]').value;
    const password = document.querySelector('#login-form input[type="password"]').value;

    try {
        const response = await apiFetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ login, password })
        });

        const data = await response.json();
        if (data.success) {
            document.getElementById('auth-section').classList.add('hidden');
            document.getElementById('dashboard-section').classList.remove('hidden');
            document.getElementById('user-display').textContent = data.user.login;
            loadFiles();
            loadSharedFiles();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        alert('Erreur de connexion au serveur: ' + error.message);
    }
});

document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const login = document.querySelector('#register-form input[type="text"]').value;
    const password = document.querySelector('#register-form input[type="password"]').value;

    try {
        const response = await apiFetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ login, password })
        });

        const data = await response.json();
        if (data.success) {
            document.getElementById('auth-section').classList.add('hidden');
            document.getElementById('dashboard-section').classList.remove('hidden');
            document.getElementById('user-display').textContent = data.user.login;
            loadFiles();
            loadSharedFiles();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        alert('Erreur de connexion au serveur: ' + error.message);
    }
});

async function logout() {
    try {
        await apiFetch('/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (error) {
        console.error('Erreur lors de la deconnexion:', error);
    }

    document.getElementById('auth-section').classList.remove('hidden');
    document.getElementById('dashboard-section').classList.add('hidden');
    document.querySelectorAll('input').forEach(input => input.value = '');
}

async function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];

    if (!file) {
        alert('Veuillez selectionner un fichier');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await apiFetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (data.success) {
            alert('Fichier "' + data.file.name + '" uploade avec succes !');
            fileInput.value = '';
            loadFiles();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        alert('Erreur lors de l\'upload: ' + error.message);
    }
}

async function loadFiles() {
    try {
        const response = await apiFetch('/files');
        const data = await response.json();

        if (data.success) {
            const tbody = document.querySelector('#files-table tbody');
            tbody.innerHTML = '';

            data.files.forEach(file => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${file.name}</td>
                    <td>${formatDate(file.date)}</td>
                    <td>
                        <button onclick="downloadFile(${file.id})" class="btn-primary" style="width: auto; padding: 5px 10px; margin: 2px;">
                            Telecharger
                        </button>
                        <button onclick="shareFile(${file.id})" class="btn-success" style="width: auto; padding: 5px 10px; margin: 2px;">
                            Partager
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('Erreur lors du chargement des fichiers:', error);
    }
}

async function downloadFile(fileId) {
    try {
        const response = await apiFetch(`/download/${fileId}`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'fichier';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const data = await response.json();
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        alert('Erreur lors du telechargement: ' + error.message);
    }
}

function shareFile(fileId) {
    const username = prompt('Entrez le nom d\'utilisateur avec qui partager ce fichier:');
    if (username) {
        shareFileWithUser(fileId, username);
    }
}

async function shareFileWithUser(fileId, username) {
    try {
        const response = await apiFetch('/share', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: fileId,
                recipient_login: username
            })
        });

        const data = await response.json();
        if (data.success) {
            alert(data.message);
            loadSharedFiles();
        } else {
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        alert('Erreur lors du partage: ' + error.message);
    }
}

async function loadSharedFiles() {
    try {
        const response = await apiFetch('/shared-files');
        const data = await response.json();

        if (data.success) {
            const tbody = document.querySelector('#shared-files-table tbody');
            if (tbody) {
                tbody.innerHTML = '';

                data.files.forEach(file => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${file.name}</td>
                        <td>${file.owner}</td>
                        <td>${formatDate(file.date)}</td>
                        <td>
                            <button onclick="downloadSharedFile(${file.id})" class="btn-primary" style="width: auto; padding: 5px 10px; margin: 2px;">
                                Telecharger
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            }
        }
    } catch (error) {
        console.error('Erreur lors du chargement des fichiers partages:', error);
    }
}

async function downloadSharedFile(fileId) {
    try {
        const response = await apiFetch(`/download-shared/${fileId}`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'fichier_partage';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const data = await response.json();
            alert('Erreur: ' + data.message);
        }
    } catch (error) {
        alert('Erreur lors du telechargement du fichier partage: ' + error.message);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR') + ' ' + date.toLocaleTimeString('fr-FR');
}

document.addEventListener('DOMContentLoaded', () => {
    apiFetch('/user')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('auth-section').classList.add('hidden');
                document.getElementById('dashboard-section').classList.remove('hidden');
                document.getElementById('user-display').textContent = data.user.login;
                loadFiles();
                loadSharedFiles();
            }
        })
        .catch(() => {
            console.log('Utilisateur non connecte');
        });
});

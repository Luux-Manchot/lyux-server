/**
 * LyuX Cockpit Extension: Nettoyage et Catégorisation intelligente des groupes scolaires
 */
(function() {
    'use strict';

    let currentFilter = '';

    function getGroupCategory(name) {
        const n = name.toLowerCase();
        if (/^(1g|2nde|tg|term|premiere|seconde|bts|cap|bac)/i.test(n) || /^[0-9]+[a-z]+[0-9]*/i.test(n)) {
            return 'classes';
        }
        if (n.includes('enseignant') || n.includes('prof')) {
            return 'profs';
        }
        if (n === 'eleves') {
            return 'eleves';
        }
        if (n.includes('direction') || n.includes('viesco') || n.includes('administration')) {
            return 'direction';
        }
        if (n.includes('sudo') || n.includes('root') || n.includes('docker') || n.includes('technicien') || n.includes('informatique')) {
            return 'tech';
        }
        return 'system';
    }

    function filterCockpitAccounts(searchTerm) {
        const input = document.getElementById('accounts-filter');
        if (!input) return;

        currentFilter = searchTerm;
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(input, searchTerm);
        input.dispatchEvent(new Event('input', { bubbles: true }));

        updateActivePillState();
    }

    function updateActivePillState() {
        document.querySelectorAll('.lyux-cat-pill').forEach(pill => {
            const groupName = pill.getAttribute('data-group');
            if (groupName && currentFilter && groupName.toLowerCase() === currentFilter.toLowerCase()) {
                pill.classList.add('is-active');
            } else {
                pill.classList.remove('is-active');
            }
        });

        const activeIndicator = document.getElementById('lyux-active-filter-indicator');
        if (activeIndicator) {
            if (currentFilter) {
                activeIndicator.innerHTML = `
                    <span style="font-size: 12px; font-weight: 600; color: #0066cc;">
                        Filtre actif : <strong>${currentFilter.toUpperCase()}</strong>
                    </span>
                    <button id="lyux-clear-filter-btn" style="border: 1px solid #b8d4f0; background: #e7f1fa; color: #004080; border-radius: 12px; padding: 2px 8px; font-size: 11px; font-weight: 700; cursor: pointer;">
                        ✕ Afficher tout
                    </button>
                `;
                activeIndicator.style.display = 'inline-flex';
                document.getElementById('lyux-clear-filter-btn')?.addEventListener('click', () => {
                    filterCockpitAccounts('');
                });
            } else {
                activeIndicator.style.display = 'none';
            }
        }
    }

    async function fetchCleanGroups() {
        try {
            if (window.cockpit && cockpit.file) {
                const groupContent = await cockpit.file('/etc/group').read();
                const lines = groupContent.split('\n');
                const groups = [];
                for (const line of lines) {
                    const parts = line.split(':');
                    if (parts.length >= 4) {
                        const name = parts[0];
                        const gid = parseInt(parts[2], 10);
                        const members = parts[3] ? parts[3].split(',').filter(Boolean) : [];
                        // On ne garde que les groupes utiles (gid >= 1000 ou avec membres ou sudo/root)
                        if (gid >= 1000 || members.length > 0 || ['sudo', 'docker', 'users'].includes(name)) {
                            groups.push({ name, membersCount: members.length });
                        }
                    }
                }
                return groups;
            }
        } catch(e) {}

        return [
            { name: "1g1", membersCount: 2 },
            { name: "1g2", membersCount: 2 },
            { name: "eleves", membersCount: 4 },
            { name: "enseignants", membersCount: 2 },
            { name: "profs_maths", membersCount: 1 },
            { name: "profs_sciences", membersCount: 1 },
            { name: "direction", membersCount: 1 },
            { name: "viescolaire", membersCount: 1 },
            { name: "administration", membersCount: 2 },
            { name: "sudo", membersCount: 2 },
            { name: "docker", membersCount: 1 },
            { name: "informatique", membersCount: 1 }
        ];
    }

    async function injectCategoriesUI() {
        if (document.getElementById('lyux-categories-container')) return;

        const groupsCard = document.querySelector('.ct-card');
        if (!groupsCard) return;

        const groups = await fetchCleanGroups();
        const categorized = {
            classes: [],
            profs: [],
            direction: [],
            tech: []
        };

        groups.forEach(g => {
            const cat = getGroupCategory(g.name);
            if (cat === 'classes') categorized.classes.push(g);
            else if (cat === 'profs') categorized.profs.push(g);
            else if (cat === 'direction') categorized.direction.push(g);
            else if (cat === 'tech') categorized.tech.push(g);
        });

        const container = document.createElement('div');
        container.id = 'lyux-categories-container';
        container.style.cssText = `
            padding: 12px 16px;
            background: #ffffff;
            border-top: 1px solid #e0e0e0;
            display: flex;
            flex-direction: column;
            gap: 10px;
            font-size: 13px;
        `;

        const style = document.createElement('style');
        style.textContent = `
            .lyux-cat-row {
                display: flex;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
            }
            .lyux-cat-title {
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                color: #6a6e73;
                min-width: 120px;
            }
            .lyux-cat-pill {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                padding: 3px 10px;
                border-radius: 14px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                user-select: none;
                transition: all 0.15s ease;
                border: 1px solid transparent;
            }
            .lyux-cat-pill:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .lyux-cat-pill.is-active {
                outline: 2px solid #0066cc;
                font-weight: 700;
            }
            .pill-classe {
                background: #e7f1fa;
                color: #004080;
                border-color: #bee1f4;
            }
            .pill-classe.is-active {
                background: #0066cc;
                color: #ffffff;
            }
            .pill-prof {
                background: #f2f0f9;
                color: #4a2c7a;
                border-color: #cfc6e8;
            }
            .pill-prof.is-active {
                background: #6753ac;
                color: #ffffff;
            }
            .pill-staff {
                background: #edf8f0;
                color: #1e8449;
                border-color: #bde7c7;
            }
            .pill-staff.is-active {
                background: #3e8635;
                color: #ffffff;
            }
            .pill-tech {
                background: #fef3d6;
                color: #795600;
                border-color: #f6d173;
            }
        `;
        document.head.appendChild(style);

        const totalStudents = categorized.classes.reduce((sum, c) => sum + c.membersCount, 0);

        container.innerHTML = `
            <!-- Classes Scolaires (chaque élève dans sa classe) -->
            <div class="lyux-cat-row">
                <span class="lyux-cat-title">🏫 Classes :</span>
                ${categorized.classes.map(c => `
                    <span class="lyux-cat-pill pill-classe" data-group="${c.name}" onclick="window.__lyuxFilter('${c.name}')">
                        🏫 ${c.name.toUpperCase()} <span style="font-size: 10px; opacity: 0.85;">(${c.membersCount} élèves)</span>
                    </span>
                `).join('')}
                <span class="lyux-cat-pill pill-classe" data-group="eleves" onclick="window.__lyuxFilter('eleves')" style="border-style: dashed;">
                    🎒 Tous les élèves (${totalStudents})
                </span>
            </div>

            <!-- Corps Enseignant & Matières -->
            <div class="lyux-cat-row">
                <span class="lyux-cat-title">👨‍🏫 Pédagogie :</span>
                <span class="lyux-cat-pill pill-prof" data-group="enseignants" onclick="window.__lyuxFilter('enseignants')">
                    👨‍🏫 Tous les profs
                </span>
                ${categorized.profs.map(p => `
                    <span class="lyux-cat-pill pill-prof" data-group="${p.name}" onclick="window.__lyuxFilter('${p.name}')">
                        📐 ${p.name.replace('profs_', '')} <span style="font-size: 10px; opacity: 0.85;">(${p.membersCount})</span>
                    </span>
                `).join('')}
            </div>

            <!-- Direction & Vie Scolaire -->
            <div class="lyux-cat-row">
                <span class="lyux-cat-title">🏛️ Établissement :</span>
                ${categorized.direction.map(d => `
                    <span class="lyux-cat-pill pill-staff" data-group="${d.name}" onclick="window.__lyuxFilter('${d.name}')">
                        🏛️ ${d.name} <span style="font-size: 10px; opacity: 0.85;">(${d.membersCount})</span>
                    </span>
                `).join('')}
                <span class="lyux-cat-pill pill-tech" data-group="sudo" onclick="window.__lyuxFilter('sudo')">
                    💻 admin (sudo)
                </span>
            </div>

            <!-- Filtre actif -->
            <div id="lyux-active-filter-indicator" style="display: none; align-items: center; gap: 8px; margin-top: 4px; padding-top: 6px; border-top: 1px dashed #e0e0e0;"></div>
        `;

        groupsCard.appendChild(container);

        window.__lyuxFilter = function(groupName) {
            if (currentFilter && currentFilter.toLowerCase() === groupName.toLowerCase()) {
                filterCockpitAccounts('');
            } else {
                filterCockpitAccounts(groupName);
            }
        };
    }

    function enhanceTableBadges() {
        const table = document.getElementById('accounts-list');
        if (!table) return;

        const cells = table.querySelectorAll('td');
        cells.forEach(td => {
            const labels = td.querySelectorAll('.pf-v6-c-label, [class*="label"], [class*="badge"]');
            labels.forEach(lbl => {
                const text = lbl.innerText.trim().toLowerCase();
                if (text === '1g1') {
                    lbl.innerHTML = '🏫 1G1';
                    lbl.style.cssText = 'background: #e7f1fa !important; color: #004080 !important; font-weight: 700; border: 1px solid #bee1f4; cursor: pointer;';
                    lbl.onclick = (e) => { e.stopPropagation(); window.__lyuxFilter('1g1'); };
                } else if (text === '1g2') {
                    lbl.innerHTML = '🏫 1G2';
                    lbl.style.cssText = 'background: #e7f1fa !important; color: #004080 !important; font-weight: 700; border: 1px solid #bee1f4; cursor: pointer;';
                    lbl.onclick = (e) => { e.stopPropagation(); window.__lyuxFilter('1g2'); };
                } else if (text === 'eleves') {
                    lbl.innerHTML = '🎒 élève';
                } else if (text === 'enseignants') {
                    lbl.innerHTML = '👨‍🏫 enseignant';
                    lbl.style.cssText = 'background: #f2f0f9 !important; color: #4a2c7a !important; font-weight: 700; cursor: pointer;';
                    lbl.onclick = (e) => { e.stopPropagation(); window.__lyuxFilter('enseignants'); };
                } else if (text.startsWith('profs_')) {
                    lbl.innerHTML = '📐 ' + text.replace('profs_', '');
                } else if (text === 'direction' || text === 'viescolaire' || text === 'viesco') {
                    lbl.innerHTML = '🏛️ ' + text;
                }
            });
        });
    }

    const observer = new MutationObserver(() => {
        injectCategoriesUI();
        enhanceTableBadges();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            injectCategoriesUI();
            enhanceTableBadges();
        });
    } else {
        injectCategoriesUI();
        enhanceTableBadges();
    }
})();

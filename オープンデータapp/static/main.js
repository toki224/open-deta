

// 初期化処理
window.onload = function() {
    fetchLineOptions();
};

function fetchLineOptions() {
    fetch('http://127.0.0.1:8000/lines')
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById('lineNameSelect');
            data.forEach(line => {
                const option = document.createElement('option');
                option.value = line;
                option.textContent = line;
                select.appendChild(option);
            });
        })
        .catch(err => console.error("路線リスト取得エラー:", err));
}


window.handleEnter = function(e) {
    if(e.key === 'Enter') searchStations();
};


window.changeCategory = function() {
    
    const val = document.getElementById('categorySelect').value;
    const banner = document.getElementById('categoryBanner');
    const bannerText = document.getElementById('categoryBannerText');
    const bannerIcon = document.getElementById('bannerIcon');
    const searchBtn = document.getElementById('searchBtn');

    document.querySelectorAll('.filter-section').forEach(el => {
        el.classList.remove('active');
        el.querySelectorAll('input').forEach(box => box.checked = false);
    });

    if (val === "") {
        banner.classList.remove('active');
        searchBtn.disabled = true;
        searchBtn.textContent = "カテゴリーを選択してください";
    } else {
        banner.classList.add('active');
        searchBtn.disabled = false;
        searchBtn.textContent = "検索する";

        if (val === "physical") {
            document.getElementById('filters-physical').classList.add('active');
            bannerText.textContent = "身体障害（車椅子・移動）";
            bannerIcon.className = "fa-solid fa-wheelchair";
        } else if (val === "hearing") {
            document.getElementById('filters-hearing').classList.add('active');
            bannerText.textContent = "聴覚障害（情報・案内）";
            bannerIcon.className = "fa-solid fa-ear-listen";
        }
    }
};


window.searchStations = function() {
    const listContainer = document.getElementById('stationList');
    
    const stationName = document.getElementById('stationNameInput').value.trim();

    const lineName = document.getElementById('lineNameSelect').value;
    
    const params = new URLSearchParams();
    if(stationName) params.append('name', stationName);
    if(lineName) params.append('line_name', lineName); // ★追加

    const activeSection = document.querySelector('.filter-section.active');
    let checkedKeys = [];

    if (activeSection) {
        const checks = activeSection.querySelectorAll('.filter-check:checked');
        checks.forEach(c => {
            params.append(c.value, 'true');
            checkedKeys.push(c.value);
        });
    }

    listContainer.innerHTML = '<div style="text-align:center; padding:40px;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><br>検索中...</div>';

    fetch(`http://127.0.0.1:8000/stations?${params.toString()}`)
        .then(async res => {
            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`Server Error: ${res.status} ${errorText}`);
            }
            return res.json();
        })
        .then(data => {
            listContainer.innerHTML = '';

            if (!data || data.length === 0) {
                listContainer.innerHTML = '<div style="text-align:center; padding:20px;">条件に一致する駅が見つかりませんでした。</div>';
                return;
            }

            const countLi = document.createElement('li');
            countLi.style.padding = '10px 20px';
            countLi.style.fontWeight = 'bold';
            countLi.style.backgroundColor = '#f9f9f9';
            countLi.style.borderBottom = '1px solid #ddd';
            countLi.style.color = '#555';
            countLi.textContent = `検索結果: ${data.length}件`;
            listContainer.appendChild(countLi);

            data.forEach(station => {
                const li = document.createElement('li');
                li.className = 'station-item-simple';

                let htmlContent = `<div class="simple-station-name">${station.name}駅</div>`;
                
                if (checkedKeys.length > 0) {
                    htmlContent += `<div class="station-status-row">`;
                    checkedKeys.forEach(key => {
                        const val = station[key];
                        
                        if(val === undefined) return;

                        const def = getLabelDef(key);
                        let displayVal = val;
                        let statusClass = 'status-ok';

                        if (val === true) displayVal = '○';

                        htmlContent += `
                            <div class="status-chip">
                                <i class="fa-solid ${def.icon}"></i> ${def.label}: 
                                <span class="${statusClass}">${displayVal}</span>
                            </div>
                        `;
                    });
                    htmlContent += `</div>`;
                } else {
                    htmlContent += `<i class="fa-solid fa-chevron-right arrow-icon"></i>`;
                }

                li.innerHTML = htmlContent;
                listContainer.appendChild(li);
            });
        })
        .catch(err => {
            console.error(err);
            listContainer.innerHTML = `<div style="color:red; text-align:center; padding:20px;">エラーが発生しました。<br>${err.message}</div>`;
        });
};

function getLabelDef(key) {
    const labels = {
        step_free: { label: "段差", icon: "fa-stairs" },
        platform_count: { label: "ホーム", icon: "fa-train" },
        step_free_platform_count: { label: "段差解消H", icon: "fa-check-double" },
        elevator_count: { label: "EV", icon: "fa-elevator" },
        compliant_elevator_count: { label: "適合EV", icon: "fa-elevator" },
        escalator_count: { label: "ES", icon: "fa-up-down" },
        compliant_escalator_count: { label: "適合ES", icon: "fa-up-down" },
        other_lift_count: { label: "他昇降機", icon: "fa-arrows-up-down" },
        slope_count: { label: "傾斜路", icon: "fa-wheelchair" },
        compliant_slope_count: { label: "適合傾斜路", icon: "fa-wheelchair" },
        info_facility: { label: "案内", icon: "fa-info-circle" },
        toilet: { label: "トイレ", icon: "fa-restroom" },
        ticket_gate: { label: "改札", icon: "fa-ticket" },
        wheelchair_platform_count: { label: "車椅子H", icon: "fa-wheelchair-move" },
        fall_prevention: { label: "転落防止", icon: "fa-dungeon" }
    };
    return labels[key] || { label: key, icon: "fa-circle" };
}
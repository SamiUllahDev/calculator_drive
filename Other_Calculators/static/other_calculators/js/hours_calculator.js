let currentMode = 'time_difference';
let hoursChart = null;

function switchMode(mode) {
    if (!mode) return;
    
    currentMode = mode;
    
    // Update dropdown
    const selector = document.getElementById('calc-mode-selector');
    if (selector) selector.value = mode;
    
    // Show/hide form sections
    document.querySelectorAll('[role="tabpanel"]').forEach(panel => panel.classList.add('hidden'));
    const formSection = document.getElementById(`form-${mode}`);
    if (formSection) formSection.classList.remove('hidden');
    
    // Reset results
    document.getElementById('resultsSection')?.classList.add('hidden');
    document.getElementById('initialState')?.classList.remove('hidden');
    document.getElementById('errorState')?.classList.add('hidden');
    if (hoursChart) {
        hoursChart.destroy();
        hoursChart = null;
    }
}

function addPeriod() {
    const container = document.getElementById('periodsContainer');
    const count = container.querySelectorAll('.period-row').length;
    
    const periodHtml = `
        <div class="period-row flex gap-2 items-center" data-id="${count + 1}">
            <input type="time" class="period-start flex-1 px-3 py-2 border-2 border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="09:00">
            <span class="text-gray-500">to</span>
            <input type="time" class="period-end flex-1 px-3 py-2 border-2 border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="17:00">
            <button type="button" class="remove-period text-red-500 hover:text-red-700 p-1 transition">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', periodHtml);
    updatePeriodCount();
}

function updatePeriodCount() {
    const count = document.querySelectorAll('#periodsContainer .period-row').length;
    const countEl = document.getElementById('periodCount');
    if (countEl) countEl.textContent = `${count} ${window.djangoContext.trans_periods_0}`;
}

function formatNumber(num) {
    if (Math.abs(num) < 0.000001) return num.toExponential(6);
    if (Math.abs(num) >= 1000000) return num.toExponential(6);
    return num.toLocaleString('en-US', {maximumFractionDigits: 2});
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function calculateHours(event) {
    if (event) event.preventDefault();
    
    const btn = document.getElementById('calculateBtn');
    const btnText = document.getElementById('calculateBtnText');
    const errorState = document.getElementById('errorState');
    const errorMessage = document.getElementById('errorMessage');
    const spinner = document.getElementById('loadingSpinner');
    const icon = document.getElementById('calculateIcon');
    
    if (!btn || !errorState || !errorMessage) return;
    
    errorState.classList.add('hidden');
    
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (!csrfToken) {
        errorMessage.textContent = window.djangoContext.trans_CSRFtokennotfoundPle_1;
        errorState.classList.remove('hidden');
        return;
    }
    
    let requestData = { calc_type: currentMode };
    const visibleForm = document.getElementById(`form-${currentMode}`);
    if (!visibleForm) {
        errorMessage.textContent = window.djangoContext.trans_Invalidcalculationty_2;
        errorState.classList.remove('hidden');
        return;
    }
    
    // Collect data based on mode
    if (currentMode === 'time_difference') {
        const startTime = document.getElementById('start_time').value;
        const endTime = document.getElementById('end_time').value;
        if (!startTime || !endTime) {
            errorMessage.textContent = window.djangoContext.trans_Pleasefillinallrequi_3;
            errorState.classList.remove('hidden');
            return;
        }
        requestData.start_time = startTime;
        requestData.end_time = endTime;
        requestData.next_day = document.getElementById('next_day').checked;
    } else if (currentMode === 'add_subtract') {
        const time = document.getElementById('time_add').value;
        const hours = parseFloat(document.getElementById('hours_add').value);
        if (!time || isNaN(hours)) {
            errorMessage.textContent = window.djangoContext.trans_Pleasefillinallrequi_3;
            errorState.classList.remove('hidden');
            return;
        }
        requestData.time = time;
        requestData.hours = hours;
        requestData.operation = document.getElementById('operation').value;
    } else if (currentMode === 'convert') {
        const value = parseFloat(document.getElementById('value_convert').value);
        if (isNaN(value)) {
            errorMessage.textContent = window.djangoContext.trans_Pleasefillinallrequi_3;
            errorState.classList.remove('hidden');
            return;
        }
        requestData.value = value;
        requestData.from_unit = document.getElementById('from_unit_convert').value;
        requestData.to_unit = document.getElementById('to_unit_convert').value;
    } else if (currentMode === 'total_hours') {
        const periods = [];
        document.querySelectorAll('#periodsContainer .period-row').forEach(row => {
            const start = row.querySelector('.period-start').value;
            const end = row.querySelector('.period-end').value;
            if (start && end) {
                periods.push({
                    start_time: start,
                    end_time: end,
                    next_day: false
                });
            }
        });
        if (periods.length === 0) {
            errorMessage.textContent = window.djangoContext.trans_Pleaseaddatleastonet_6;
            errorState.classList.remove('hidden');
            return;
        }
        requestData.time_periods = periods;
    } else if (currentMode === 'hours_worked') {
        const startTime = document.getElementById('start_time_worked').value;
        const endTime = document.getElementById('end_time_worked').value;
        if (!startTime || !endTime) {
            errorMessage.textContent = window.djangoContext.trans_Pleasefillinallrequi_3;
            errorState.classList.remove('hidden');
            return;
        }
        requestData.start_time = startTime;
        requestData.end_time = endTime;
        requestData.break_minutes = parseFloat(document.getElementById('break_minutes').value) || 0;
        requestData.next_day = document.getElementById('next_day_worked').checked;
    }
    
    btn.disabled = true;
    if (btnText) btnText.textContent = window.djangoContext.trans_Calculating_8;
    if (spinner) spinner.classList.remove('hidden');
    if (icon) icon.classList.add('hidden');
    
    try {
        const response = await fetch(window.location.href, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken.value
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        if (!data.success) {
            errorMessage.textContent = data.error || window.djangoContext.trans_Anerroroccurred_9;
            errorState.classList.remove('hidden');
            return;
        }
        
        // Show results
        document.getElementById('initialState')?.classList.add('hidden');
        document.getElementById('resultsSection')?.classList.remove('hidden');
        
        // Update result display
        let resultValue = '';
        let resultUnit = '';
        let detailsHtml = '';
        let additionalInfo = '';
        
        if (data.calc_type === 'time_difference') {
            resultValue = data.difference_time || formatNumber(data.difference_hours);
            resultUnit = 'hours';
            additionalInfo = `
                <div class="mt-3 text-sm">
                    <p>${formatNumber(data.difference_hours)} ${window.djangoContext.trans_hours_10} = ${formatNumber(data.difference_minutes)} ${window.djangoContext.trans_minutes_11} = ${formatNumber(data.difference_seconds)} ${window.djangoContext.trans_seconds_12}</p>
                </div>
            `;
            detailsHtml = `
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p class="text-2xl font-bold text-blue-600">${data.start_time}</p>
                    <p class="text-sm text-gray-600">${window.djangoContext.trans_StartTime_13}</p>
                </div>
                <div class="bg-green-50 rounded-lg p-4 border border-green-200">
                    <p class="text-2xl font-bold text-green-600">${data.end_time}</p>
                    <p class="text-sm text-gray-600">${window.djangoContext.trans_EndTime_14}</p>
                </div>
            `;
        } else if (data.calc_type === 'add_subtract') {
            resultValue = data.result_time;
            resultUnit = '';
            if (data.days !== 0) {
                additionalInfo = `
                    <div class="mt-3 text-sm">
                        <p>${Math.abs(data.days)} ${window.djangoContext.trans_days_15} ${data.days > 0 ? window.djangoContext.trans_later_16 : window.djangoContext.trans_earlier_17}</p>
                    </div>
                `;
            }
            detailsHtml = `
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p class="text-2xl font-bold text-blue-600">${formatNumber(data.result_hours)}</p>
                    <p class="text-sm text-gray-600">${window.djangoContext.trans_Hours_18}</p>
                </div>
            `;
        } else if (data.calc_type === 'convert') {
            resultValue = formatNumber(data.result);
            const unitMap = {'hours': window.djangoContext.trans_hours_10, 'minutes': window.djangoContext.trans_minutes_11, 'seconds': window.djangoContext.trans_seconds_12, 'days': window.djangoContext.trans_days_22};
            resultUnit = unitMap[data.to_unit] || data.to_unit;
            detailsHtml = `
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p class="text-2xl font-bold text-blue-600">${formatNumber(data.value)}</p>
                    <p class="text-sm text-gray-600">${window.djangoContext.trans_From_23} ${unitMap[data.from_unit] || data.from_unit}</p>
                </div>
            `;
        } else if (data.calc_type === 'total_hours') {
            resultValue = data.total_time || formatNumber(data.total_hours);
            resultUnit = 'hours';
            additionalInfo = `
                <div class="mt-3 text-sm">
                    <p>${formatNumber(data.total_hours)} ${window.djangoContext.trans_hours_10} = ${formatNumber(data.total_minutes)} ${window.djangoContext.trans_minutes_11} = ${formatNumber(data.total_days)} ${window.djangoContext.trans_days_22}</p>
                </div>
            `;
            detailsHtml = `
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p class="text-2xl font-bold text-blue-600">${data.time_periods.length}</p>
                    <p class="text-sm text-gray-600">${window.djangoContext.trans_TimePeriods_27}</p>
                </div>
            `;
        } else if (data.calc_type === 'hours_worked') {
            resultValue = data.hours_worked_time || formatNumber(data.hours_worked);
            resultUnit = 'hours';
            additionalInfo = `
                <div class="mt-3 text-sm">
                    <p>${formatNumber(data.hours_worked)} ${window.djangoContext.trans_hours_10} = ${formatNumber(data.hours_worked_minutes)} ${window.djangoContext.trans_minutes_11}</p>
                </div>
            `;
            detailsHtml = `
                <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <p class="text-2xl font-bold text-blue-600">${formatNumber(data.total_hours)}</p>
                    <p class="text-sm text-gray-600">${window.djangoContext.trans_TotalTime_30}</p>
                </div>
                <div class="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                    <p class="text-2xl font-bold text-yellow-600">${formatNumber(data.break_hours)}</p>
                    <p class="text-sm text-gray-600">${window.djangoContext.trans_BreakTime_31}</p>
                </div>
            `;
        }
        
        document.getElementById('resultValue').textContent = resultValue;
        document.getElementById('resultUnit').textContent = resultUnit;
        document.getElementById('additionalInfo').innerHTML = additionalInfo;
        document.getElementById('detailsSection').innerHTML = detailsHtml;
        
        // Chart
        if (data.chart_data) {
            const chartEl = document.getElementById('hoursChart');
            if (chartEl) {
                if (hoursChart) hoursChart.destroy();
                
                let chartConfig = null;
                if (data.chart_data.time_difference_chart) {
                    chartConfig = data.chart_data.time_difference_chart;
                } else if (data.chart_data.total_hours_chart) {
                    chartConfig = data.chart_data.total_hours_chart;
                } else if (data.chart_data.hours_worked_chart) {
                    chartConfig = data.chart_data.hours_worked_chart;
                }
                
                if (chartConfig) {
                    hoursChart = new Chart(chartEl.getContext('2d'), chartConfig);
                    document.getElementById('chartsSection').classList.remove('hidden');
                } else {
                    document.getElementById('chartsSection').classList.add('hidden');
                }
            }
        } else {
            document.getElementById('chartsSection').classList.add('hidden');
        }
        
        // Step-by-step
        const stepEl = document.getElementById('stepByStep');
        if (stepEl && data.step_by_step?.length > 0) {
            let stepNum = 0;
            stepEl.innerHTML = data.step_by_step.map(step => {
                if (!step || !step.trim()) return '<div class="my-3"></div>';
                
                const text = escapeHtml(step);
                const isStep = /^(Step\s*\d+|Step|Formula|Calculation|Result|Note|Where:)/i.test(text);
                const isFormula = /[=×÷+\-*\/]/.test(text) && (text.length < 100 || text.includes('='));
                const isResult = /^(Result|Total|Final|Answer|Time|Difference|Hours|Worked)/i.test(text);
                
                if (isStep) {
                    stepNum++;
                    return `<div class="flex items-start gap-3 mb-4 p-4 bg-white rounded-lg border-l-4 border-blue-500 shadow-sm">
                        <div class="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold text-sm">${stepNum}</div>
                        <div class="flex-1"><p class="text-gray-800 leading-relaxed">${text}</p></div>
                    </div>`;
                } else if (isFormula || text.includes('=')) {
                    return `<div class="mb-3 p-3 bg-gray-900 text-green-400 rounded-lg font-mono text-sm overflow-x-auto"><code>${text}</code></div>`;
                } else if (isResult) {
                    return `<div class="mb-4 p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-l-4 border-green-500 rounded-lg">
                        <div class="flex items-center gap-2 mb-2">
                            <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            <span class="font-semibold text-green-800">${window.djangoContext.trans_Result_32}</span>
                        </div>
                        <p class="text-gray-800 font-medium">${text}</p>
                    </div>`;
                } else {
                    return `<div class="mb-2 p-3 bg-white rounded-lg border border-gray-200"><p class="text-gray-700 leading-relaxed">${text}</p></div>`;
                }
            }).join('');
        }
        
    } catch (error) {
        console.error('Error:', error);
        if (errorState && errorMessage) {
            errorMessage.textContent = window.djangoContext.trans_AnerroroccurredPleas_33;
            errorState.classList.remove('hidden');
        }
    } finally {
        if (btn) btn.disabled = false;
        if (btnText) btnText.textContent = window.djangoContext.trans_Calculate_34;
        if (spinner) spinner.classList.add('hidden');
        if (icon) icon.classList.remove('hidden');
    }
}

function resetHours() {
    document.getElementById('start_time').value = '';
    document.getElementById('end_time').value = '';
    document.getElementById('next_day').checked = false;
    document.getElementById('time_add').value = '';
    document.getElementById('hours_add').value = '';
    document.getElementById('value_convert').value = '';
    document.getElementById('start_time_worked').value = '';
    document.getElementById('end_time_worked').value = '';
    document.getElementById('break_minutes').value = '0';
    document.getElementById('next_day_worked').checked = false;
    const container = document.getElementById('periodsContainer');
    if (container) {
        container.innerHTML = '';
        addPeriod();
        addPeriod();
    }
    switchMode('time_difference');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('initialState').classList.remove('hidden');
    document.getElementById('errorState').classList.add('hidden');
    if (hoursChart) {
        hoursChart.destroy();
        hoursChart = null;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    switchMode('time_difference');
    addPeriod();
    addPeriod();
    document.getElementById('addPeriod').addEventListener('click', addPeriod);
    document.getElementById('resetBtn').addEventListener('click', resetHours);
    document.getElementById('periodsContainer').addEventListener('click', function(e) {
        if (e.target.closest('.remove-period')) {
            const row = e.target.closest('.period-row');
            if (this.children.length > 1) {
                row.remove();
                updatePeriodCount();
            }
        }
    });
});
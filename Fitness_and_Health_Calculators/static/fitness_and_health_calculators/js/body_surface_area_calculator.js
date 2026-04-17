// Chart instances
let formulasChart = null;
let rangeChart = null;

// Check if Chart.js is loaded
function checkChartJS() {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded. Please ensure the CDN script is included.');
        return false;
    }
    return true;
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('calculatorForm');
    const unitMetric = document.getElementById('unitMetric');
    const unitImperial = document.getElementById('unitImperial');
    const heightUnit = document.getElementById('heightUnit');
    const weightUnit = document.getElementById('weightUnit');
    const heightInput = document.getElementById('height');
    const weightInput = document.getElementById('weight');
    const initialState = document.getElementById('initialState');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const results = document.getElementById('results');

    // Unit system toggle
    function updateUnitInputs() {
        if (unitImperial.checked) {
            heightUnit.textContent = 'in';
            weightUnit.textContent = 'lbs';
            heightInput.min = '20';
            heightInput.max = '100';
            heightInput.value = '67';
            weightInput.min = '2';
            weightInput.max = '1100';
            weightInput.value = '154';
        } else {
            heightUnit.textContent = 'cm';
            weightUnit.textContent = 'kg';
            heightInput.min = '50';
            heightInput.max = '250';
            heightInput.value = '170';
            weightInput.min = '1';
            weightInput.max = '500';
            weightInput.value = '70';
        }
        // Clear results when switching units
        if (results) results.classList.add('hidden');
        if (initialState) initialState.classList.remove('hidden');
    }

    unitMetric.addEventListener('change', updateUnitInputs);
    unitImperial.addEventListener('change', updateUnitInputs);

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide previous states
        if (initialState) initialState.classList.add('hidden');
        if (results) results.classList.add('hidden');
        if (errorState) errorState.classList.add('hidden');
        if (loadingState) loadingState.classList.remove('hidden');

        const formData = {
            unit_system: document.querySelector('input[name="unit_system"]:checked').value,
            height: parseFloat(heightInput.value),
            weight: parseFloat(weightInput.value)
        };

        // Update button state
        const submitBtn = document.getElementById('calculateBtnText');
        const originalText = submitBtn ? submitBtn.textContent : window.djangoContext.trans_CalculateBSA_0;
        if (submitBtn) submitBtn.textContent = window.djangoContext.trans_Calculating_1;
        document.getElementById('calculateBtn').disabled = true;

        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (loadingState) loadingState.classList.add('hidden');
            if (submitBtn) submitBtn.textContent = originalText;
            document.getElementById('calculateBtn').disabled = false;

            if (!data.success) {
                if (errorState) {
                    document.getElementById('errorMessage').textContent = data.error || window.djangoContext.trans_AnerroroccurredPleas_2;
                    errorState.classList.remove('hidden');
                }
                return;
            }

            // Display results
            displayResults(data);

        } catch (err) {
            if (loadingState) loadingState.classList.add('hidden');
            if (submitBtn) submitBtn.textContent = originalText;
            document.getElementById('calculateBtn').disabled = false;
            if (errorState) {
                document.getElementById('errorMessage').textContent = window.djangoContext.trans_Anetworkerroroccurre_3;
                errorState.classList.remove('hidden');
            }
            console.error('Error:', err);
        }
    });

    function displayResults(data) {
        try {
            // Update main result
            const averageBsaEl = document.getElementById('averageBsa');
            if (averageBsaEl) averageBsaEl.textContent = data.formulas.average.toFixed(3) + ' m²';

            // Update individual formulas
            const duBoisEl = document.getElementById('duBois');
            const mostellerEl = document.getElementById('mosteller');
            const haycockEl = document.getElementById('haycock');
            const gehanEl = document.getElementById('gehan');

            if (duBoisEl) duBoisEl.textContent = data.formulas.du_bois.toFixed(3) + ' m²';
            if (mostellerEl) mostellerEl.textContent = data.formulas.mosteller.toFixed(3) + ' m²';
            if (haycockEl) haycockEl.textContent = data.formulas.haycock.toFixed(3) + ' m²';
            if (gehanEl) gehanEl.textContent = data.formulas.gehan.toFixed(3) + ' m²';

            // Update formulas table
            const formulasTable = document.getElementById('formulasTable');
            if (formulasTable) {
                const formulas = [
                    { name: window.djangoContext.trans_DuBois_4, value: data.formulas.du_bois, note: window.djangoContext.trans_Goldstandardmostaccu_5 },
                    { name: window.djangoContext.trans_Mosteller_6, value: data.formulas.mosteller, note: window.djangoContext.trans_Simplestcommonlyused_7 },
                    { name: window.djangoContext.trans_Haycock_8, value: data.formulas.haycock, note: window.djangoContext.trans_Goodforpediatricpopu_9 },
                    { name: window.djangoContext.trans_GehanGeorge_10, value: data.formulas.gehan, note: window.djangoContext.trans_Usedinoncology_11 },
                    { name: window.djangoContext.trans_Average_12, value: data.formulas.average, note: window.djangoContext.trans_Balancedestimate_13 }
                ];
                
                formulasTable.innerHTML = formulas.map(formula => `
                    <tr class="${formula.name === ${window.djangoContext.trans_Average_12} ? 'bg-blue-50' : ''}">
                        <td class="py-2 px-3 font-medium ${formula.name === ${window.djangoContext.trans_Average_12} ? 'text-blue-900' : 'text-gray-900'}">${formula.name}</td>
                        <td class="py-2 px-3 text-right font-bold ${formula.name === ${window.djangoContext.trans_Average_12} ? 'text-blue-900' : 'text-gray-900'}">${formula.value.toFixed(3)} m²</td>
                        <td class="py-2 px-3 text-sm ${formula.name === ${window.djangoContext.trans_Average_12} ? 'text-blue-800' : 'text-gray-600'}">${formula.note}</td>
                    </tr>
                `).join('');
            }

            // Create/Update Charts
            if (data.chart_data && checkChartJS()) {
                if (data.chart_data.formulas_chart) {
                    createFormulasChart(data.chart_data.formulas_chart);
                }
                if (data.chart_data.range_chart) {
                    createRangeChart(data.chart_data.range_chart);
                }
            }

            // Show results
            if (results) {
                results.classList.remove('hidden');
                setTimeout(() => {
                    results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        } catch (error) {
            console.error('Error displaying results:', error);
            if (errorState) {
                document.getElementById('errorMessage').textContent = window.djangoContext.trans_Errordisplayingresul_18;
                errorState.classList.remove('hidden');
            }
        }
    }

    function createFormulasChart(chartData) {
        const ctx = document.getElementById('formulasChart');
        if (!ctx) return;
        if (!checkChartJS()) return;
        if (formulasChart) formulasChart.destroy();
        if (!chartData || !chartData.data) return;

        try {
            formulasChart = new Chart(ctx, {
                type: chartData.type,
                data: chartData.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `BSA: ${context.parsed.y.toFixed(3)} m²`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: '#e5e7eb' },
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(3) + ' m²';
                                },
                                font: { size: 11 }
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { size: 11, weight: 'bold' }
                            }
                        }
                    },
                    animation: { duration: 1500 }
                }
            });
        } catch (error) {
            console.error('Error creating formulas chart:', error);
        }
    }

    function createRangeChart(chartData) {
        const ctx = document.getElementById('rangeChart');
        if (!ctx) return;
        if (!checkChartJS()) return;
        if (rangeChart) rangeChart.destroy();
        if (!chartData || !chartData.data) return;

        try {
            rangeChart = new Chart(ctx, {
                type: chartData.type,
                data: chartData.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `BSA: ${context.parsed.y.toFixed(3)} m²`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: '#e5e7eb' },
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(3) + ' m²';
                                },
                                font: { size: 11 }
                            }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { size: 11, weight: 'bold' }
                            }
                        }
                    },
                    animation: { duration: 1500 }
                }
            });
        } catch (error) {
            console.error('Error creating range chart:', error);
        }
    }
});
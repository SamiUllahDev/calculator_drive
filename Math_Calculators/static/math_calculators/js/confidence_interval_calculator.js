// Chart instances
let ciChart = null;
let marginChart = null;
let proportionChart = null;

// Check if Chart.js is loaded
function checkChartJS() {
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded. Please ensure the CDN script is included.');
        return false;
    }
    return true;
}

document.addEventListener('DOMContentLoaded', function() {
    const calculatorForm = document.getElementById('calculatorForm');
    const initialState = document.getElementById('initialState');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const results = document.getElementById('results');
    const quickActions = document.getElementById('quickActions');
    const exampleBtn = document.getElementById('exampleBtn');
    
    const typeMean = document.getElementById('typeMean');
    const typeProportion = document.getElementById('typeProportion');
    const calcType = document.getElementById('calcType');
    const meanFields = document.getElementById('meanFields');
    const proportionFields = document.getElementById('proportionFields');
    const confidenceLevel = document.getElementById('confidenceLevel');
    const customConfidenceLevel = document.getElementById('customConfidenceLevel');
    
    // Calculation type toggle
    typeMean.addEventListener('click', function() {
        calcType.value = 'mean';
        meanFields.classList.remove('hidden');
        proportionFields.classList.add('hidden');
        typeMean.classList.remove('bg-gray-200', 'text-gray-700');
        typeMean.classList.add('bg-blue-600', 'text-white');
        typeProportion.classList.remove('bg-blue-600', 'text-white');
        typeProportion.classList.add('bg-gray-200', 'text-gray-700');
    });
    
    typeProportion.addEventListener('click', function() {
        calcType.value = 'proportion';
        meanFields.classList.add('hidden');
        proportionFields.classList.remove('hidden');
        typeProportion.classList.remove('bg-gray-200', 'text-gray-700');
        typeProportion.classList.add('bg-blue-600', 'text-white');
        typeMean.classList.remove('bg-blue-600', 'text-white');
        typeMean.classList.add('bg-gray-200', 'text-gray-700');
    });
    
    // Confidence level custom input
    confidenceLevel.addEventListener('change', function() {
        if (this.value === 'custom') {
            customConfidenceLevel.classList.remove('hidden');
            customConfidenceLevel.required = true;
        } else {
            customConfidenceLevel.classList.add('hidden');
            customConfidenceLevel.required = false;
        }
    });
    
    // Example values button
    if (exampleBtn) {
        exampleBtn.addEventListener('click', function() {
            if (calcType.value === 'mean') {
                document.getElementById('sampleMean').value = '50';
                document.getElementById('sampleSize').value = '100';
                document.getElementById('stdDev').value = '10';
                document.getElementById('usePopulationStd').checked = false;
            } else {
                document.getElementById('sampleProportion').value = '0.45';
                document.getElementById('proportionSampleSize').value = '200';
            }
            confidenceLevel.value = '95';
            customConfidenceLevel.classList.add('hidden');
            errorState.classList.add('hidden');
        });
    }
    
    // Form submission
    calculatorForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = {
            calc_type: calcType.value
        };
        
        if (calcType.value === 'mean') {
            formData.sample_mean = document.getElementById('sampleMean').value;
            formData.sample_size = document.getElementById('sampleSize').value;
            formData.std_dev = document.getElementById('stdDev').value;
            formData.use_population_std = document.getElementById('usePopulationStd').checked;
        } else {
            formData.sample_proportion = document.getElementById('sampleProportion').value;
            formData.sample_size = document.getElementById('proportionSampleSize').value;
        }
        
        // Get confidence level
        if (confidenceLevel.value === 'custom') {
            formData.confidence_level = customConfidenceLevel.value;
        } else {
            formData.confidence_level = confidenceLevel.value;
        }
        
        // Validate required fields
        if (calcType.value === 'mean') {
            if (!formData.sample_mean || !formData.sample_size || !formData.std_dev) {
                errorState.classList.remove('hidden');
                document.getElementById('errorMessage').textContent = window.djangoContext.trans_Pleasefillinallrequi_0;
                return;
            }
        } else {
            if (!formData.sample_proportion || !formData.sample_size) {
                errorState.classList.remove('hidden');
                document.getElementById('errorMessage').textContent = window.djangoContext.trans_Pleasefillinallrequi_0;
                return;
            }
        }
        
        // Hide previous states
        if (initialState) initialState.classList.add('hidden');
        if (results) results.classList.add('hidden');
        if (errorState) errorState.classList.add('hidden');
        if (loadingState) loadingState.classList.remove('hidden');
        
        // Update button state
        const submitBtn = document.getElementById('calculateBtnText');
        const originalText = submitBtn ? submitBtn.textContent : 'Calculate';
        if (submitBtn) submitBtn.textContent = window.djangoContext.trans_Calculating_2;
        
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
            
            if (!data.success) {
                if (errorState) {
                    document.getElementById('errorMessage').textContent = data.error || window.djangoContext.trans_AnerroroccurredPleas_3;
                    errorState.classList.remove('hidden');
                }
                return;
            }
            
            // Display results
            displayResults(data);
            
        } catch (err) {
            if (loadingState) loadingState.classList.add('hidden');
            if (submitBtn) submitBtn.textContent = originalText;
            if (errorState) {
                document.getElementById('errorMessage').textContent = window.djangoContext.trans_Anetworkerroroccurre_4;
                errorState.classList.remove('hidden');
            }
            console.error('Error:', err);
        }
    });
    
    function displayResults(data) {
        try {
            if (!data || !data.success) {
                throw new Error('Invalid data received');
            }
            
            const resultData = data.result_data || {};
            const displayData = data.display_data || {};
            const calcType = data.calc_type || 'mean';
            
            // Update confidence interval result
            const ciResult = document.getElementById('ciResult');
            const ciInterpretation = document.getElementById('ciInterpretation');
            
            if (ciResult && resultData.lower_bound !== undefined && resultData.upper_bound !== undefined) {
                const lower = resultData.lower_bound.toFixed(6);
                const upper = resultData.upper_bound.toFixed(6);
                ciResult.textContent = `[${lower}, ${upper}]`;
            }
            
            if (ciInterpretation && resultData.confidence_level) {
                const confidencePercent = (resultData.confidence_level * 100).toFixed(1);
                ciInterpretation.textContent = `${window.djangoContext.trans_Weare_5} ${confidencePercent}% ${window.djangoContext.trans_confidentthatthetrue_6} ${calcType === 'mean' ? ${window.djangoContext.trans_mean_7} : ${window.djangoContext.trans_proportion_8}} ${window.djangoContext.trans_lieswithinthisinterv_9}`;
            }
            
            // Update detailed results
            const detailedResultsEl = document.getElementById('detailedResults');
            if (detailedResultsEl && displayData.formatted_results && displayData.formatted_results.length > 0) {
                let detailsHTML = '';
                
                displayData.formatted_results.forEach((item) => {
                    const isPrimary = item.is_primary;
                    const borderClass = isPrimary ? 'border-2 border-blue-200' : 'border border-gray-200';
                    const bgClass = isPrimary ? 'bg-blue-50' : 'bg-gray-50';
                    
                    detailsHTML += `
                        <div class="${bgClass} ${borderClass} rounded-lg p-4">
                            <div class="flex justify-between items-center">
                                <h4 class="font-bold text-gray-900">${item.label}</h4>
                                <span class="text-lg font-semibold text-blue-600">${item.value}</span>
                            </div>
                        </div>
                    `;
                });
                detailedResultsEl.innerHTML = detailsHTML;
            }
            
            // Step-by-step solution
            const stepByStepEl = document.getElementById('stepByStep');
            if (stepByStepEl) {
                if (data.step_by_step_html && Array.isArray(data.step_by_step_html) && data.step_by_step_html.length > 0) {
                    stepByStepEl.innerHTML = data.step_by_step_html.map((item) => `
                        <div class="bg-gradient-to-r from-blue-50 to-blue-100 border-l-4 border-blue-500 p-4 my-2 rounded">
                            <span class="font-semibold text-blue-600">${item.content}</span>
                        </div>
                    `).join('');
                } else if (data.step_by_step && Array.isArray(data.step_by_step) && data.step_by_step.length > 0) {
                    stepByStepEl.innerHTML = data.step_by_step.map((step) => `
                        <div class="bg-gradient-to-r from-blue-50 to-blue-100 border-l-4 border-blue-500 p-4 my-2 rounded">
                            <span class="font-semibold text-blue-600">${step}</span>
                        </div>
                    `).join('');
                }
            }
            
            // Create/Update Charts
            const chartsContainer = document.getElementById('chartsContainer');
            if (chartsContainer && data.chart_data && typeof data.chart_data === 'object' && checkChartJS()) {
                try {
                    // Destroy existing charts
                    if (ciChart) {
                        ciChart.destroy();
                        ciChart = null;
                    }
                    if (marginChart) {
                        marginChart.destroy();
                        marginChart = null;
                    }
                    if (proportionChart) {
                        proportionChart.destroy();
                        proportionChart = null;
                    }
                    
                    chartsContainer.innerHTML = '';
                    
                    if (calcType === 'mean') {
                        if (data.chart_data.ci_chart && data.chart_data.ci_chart.data) {
                            const chartDiv = document.createElement('div');
                            chartDiv.className = 'bg-white rounded-xl p-4 sm:p-6 border-2 border-gray-200 shadow-lg';
                            chartDiv.innerHTML = `
                                <h3 class="text-lg font-bold text-gray-800 mb-4 text-center">${window.djangoContext.trans_ConfidenceIntervalVi_10}</h3>
                                <div class="relative h-[300px] min-h-[300px]">
                                    <canvas id="ciChart"></canvas>
                                </div>
                            `;
                            chartsContainer.appendChild(chartDiv);
                            createCIChart(data.chart_data.ci_chart);
                        }
                        
                        if (data.chart_data.margin_chart && data.chart_data.margin_chart.data) {
                            const chartDiv = document.createElement('div');
                            chartDiv.className = 'bg-white rounded-xl p-4 sm:p-6 border-2 border-gray-200 shadow-lg';
                            chartDiv.innerHTML = `
                                <h3 class="text-lg font-bold text-gray-800 mb-4 text-center">${window.djangoContext.trans_MarginofError_11}</h3>
                                <div class="relative h-[300px] min-h-[300px]">
                                    <canvas id="marginChart"></canvas>
                                </div>
                            `;
                            chartsContainer.appendChild(chartDiv);
                            createMarginChart(data.chart_data.margin_chart);
                        }
                    } else if (calcType === 'proportion') {
                        if (data.chart_data.proportion_chart && data.chart_data.proportion_chart.data) {
                            const chartDiv = document.createElement('div');
                            chartDiv.className = 'bg-white rounded-xl p-4 sm:p-6 border-2 border-gray-200 shadow-lg';
                            chartDiv.innerHTML = `
                                <h3 class="text-lg font-bold text-gray-800 mb-4 text-center">${window.djangoContext.trans_ProportionConfidence_12}</h3>
                                <div class="relative h-[300px] min-h-[300px]">
                                    <canvas id="proportionChart"></canvas>
                                </div>
                            `;
                            chartsContainer.appendChild(chartDiv);
                            createProportionChart(data.chart_data.proportion_chart);
                        }
                    }
                } catch (chartError) {
                    console.error('Error creating charts:', chartError);
                }
            }
            
            // Show results and quick actions
            if (results) {
                results.classList.remove('hidden');
                if (quickActions) {
                    quickActions.classList.remove('hidden');
                }
                setTimeout(() => {
                    results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        } catch (error) {
            console.error('Error displaying results:', error);
            if (errorState) {
                document.getElementById('errorMessage').textContent = window.djangoContext.trans_Errordisplayingresul_13;
                errorState.classList.remove('hidden');
            }
        }
    }
    
    function createCIChart(chartData) {
        const ctx = document.getElementById('ciChart');
        if (!ctx || !checkChartJS()) return;
        
        if (ciChart) ciChart.destroy();
        
        if (!chartData || !chartData.data) return;
        
        try {
            ciChart = new Chart(ctx, {
                type: chartData.type,
                data: chartData.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.parsed.y.toFixed(6)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    },
                    animation: { duration: 1500 }
                }
            });
        } catch (error) {
            console.error('Error creating CI chart:', error);
        }
    }
    
    function createMarginChart(chartData) {
        const ctx = document.getElementById('marginChart');
        if (!ctx || !checkChartJS()) return;
        
        if (marginChart) marginChart.destroy();
        
        if (!chartData || !chartData.data) return;
        
        try {
            marginChart = new Chart(ctx, {
                type: chartData.type,
                data: chartData.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { 
                            display: true,
                            position: 'bottom'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${context.parsed.toFixed(6)}`;
                                }
                            }
                        }
                    },
                    animation: { duration: 1500 }
                }
            });
        } catch (error) {
            console.error('Error creating margin chart:', error);
        }
    }
    
    function createProportionChart(chartData) {
        const ctx = document.getElementById('proportionChart');
        if (!ctx || !checkChartJS()) return;
        
        if (proportionChart) proportionChart.destroy();
        
        if (!chartData || !chartData.data) return;
        
        try {
            proportionChart = new Chart(ctx, {
                type: chartData.type,
                data: chartData.data,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.parsed.y.toFixed(6)} (${(context.parsed.y * 100).toFixed(2)}%)`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1,
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(2);
                                }
                            }
                        }
                    },
                    animation: { duration: 1500 }
                }
            });
        } catch (error) {
            console.error('Error creating proportion chart:', error);
        }
    }
    
    // Clear button
    const clearBtn = document.getElementById('clearBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            calculatorForm.reset();
            if (results) results.classList.add('hidden');
            if (initialState) initialState.classList.remove('hidden');
            if (quickActions) quickActions.classList.add('hidden');
            if (errorState) errorState.classList.add('hidden');
            
            // Reset calculation type
            calcType.value = 'mean';
            meanFields.classList.remove('hidden');
            proportionFields.classList.add('hidden');
            typeMean.classList.remove('bg-gray-200', 'text-gray-700');
            typeMean.classList.add('bg-blue-600', 'text-white');
            typeProportion.classList.remove('bg-blue-600', 'text-white');
            typeProportion.classList.add('bg-gray-200', 'text-gray-700');
            
            // Destroy charts
            if (ciChart) {
                ciChart.destroy();
                ciChart = null;
            }
            if (marginChart) {
                marginChart.destroy();
                marginChart = null;
            }
            if (proportionChart) {
                proportionChart.destroy();
                proportionChart = null;
            }
            
            document.getElementById('chartsContainer').innerHTML = '';
        });
    }
    
    // Copy button
    const copyBtn = document.getElementById('copyBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', async function() {
            const resultsElement = document.getElementById('results');
            if (!resultsElement || resultsElement.classList.contains('hidden')) {
                alert(window.djangoContext.trans_Pleasecalculatefirst_14);
                return;
            }
            
            const ciResult = document.getElementById('ciResult');
            const ciInterpretation = document.getElementById('ciInterpretation');
            
            if (!ciResult || !ciInterpretation) {
                alert(window.djangoContext.trans_UnabletocopyPleasetr_15);
                return;
            }
            
            const resultText = `Confidence Interval: ${ciResult.textContent}\n${ciInterpretation.textContent}`;
            
            try {
                await navigator.clipboard.writeText(resultText);
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = window.djangoContext.trans_Copied_16;
                copyBtn.classList.remove('bg-blue-100', 'text-blue-700');
                copyBtn.classList.add('bg-green-100', 'text-green-700');
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                    copyBtn.classList.remove('bg-green-100', 'text-green-700');
                    copyBtn.classList.add('bg-blue-100', 'text-blue-700');
                }, 2000);
            } catch (error) {
                console.error('Failed to copy:', error);
                alert(window.djangoContext.trans_Failedtocopytoclipbo_17);
            }
        });
    }
});
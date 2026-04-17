document.addEventListener('DOMContentLoaded', function() {
    const tabMode1 = document.getElementById('tabMode1');
    const tabMode2 = document.getElementById('tabMode2');
    const formMode1 = document.getElementById('formMode1');
    const formMode2 = document.getElementById('formMode2');
    const form1 = document.getElementById('calculatorForm1');
    const form2 = document.getElementById('calculatorForm2');
    
    const initialState = document.getElementById('initialState');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const resultsState = document.getElementById('resultsState');
    
    // Mode tabs
    tabMode1.addEventListener('click', function() {
        tabMode1.classList.add('text-blue-600', 'border-blue-600');
        tabMode1.classList.remove('text-gray-500', 'border-transparent');
        tabMode2.classList.remove('text-blue-600', 'border-blue-600');
        tabMode2.classList.add('text-gray-500', 'border-transparent');
        formMode1.classList.remove('hidden');
        formMode2.classList.add('hidden');
    });
    
    tabMode2.addEventListener('click', function() {
        tabMode2.classList.add('text-blue-600', 'border-blue-600');
        tabMode2.classList.remove('text-gray-500', 'border-transparent');
        tabMode1.classList.remove('text-blue-600', 'border-blue-600');
        tabMode1.classList.add('text-gray-500', 'border-transparent');
        formMode2.classList.remove('hidden');
        formMode1.classList.add('hidden');
    });
    
    // Extra options toggles
    document.querySelectorAll('input[name="repayment_option1"]').forEach(r => {
        r.addEventListener('change', () => document.getElementById('extraOptions1').classList.toggle('hidden', r.value !== 'extra' || !r.checked));
    });
    document.querySelectorAll('input[name="repayment_option2"]').forEach(r => {
        r.addEventListener('change', () => document.getElementById('extraOptions2').classList.toggle('hidden', r.value !== 'extra' || !r.checked));
    });
    
    function formatCurrency(num) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(num);
    }
    
    function parseNumber(val) {
        return parseFloat(String(val).replace(/[,$\s]/g, '')) || 0;
    }
    
    function showState(state) {
        [initialState, loadingState, errorState, resultsState].forEach(s => s.classList.add('hidden'));
        state.classList.remove('hidden');
    }
    
    // Toggle schedule
    document.getElementById('toggleSchedule').addEventListener('click', function() {
        document.getElementById('scheduleContainer').classList.toggle('hidden');
        document.getElementById('scheduleIcon').classList.toggle('rotate-180');
    });
    
    async function handleSubmit(e, formNum) {
        e.preventDefault();
        showState(loadingState);
        
        const form = formNum === 1 ? form1 : form2;
        const repaymentOption = form.querySelector(`input[name="repayment_option${formNum}"]:checked`).value;
        
        const formData = {
            calc_mode: formNum === 1 ? 'mode1' : 'mode2',
            repayment_option: repaymentOption,
        };
        
        if (formNum === 1) {
            formData.original_amount = parseNumber(document.getElementById('original_amount').value);
            formData.original_term = parseInt(document.getElementById('original_term').value);
            formData.interest_rate = parseNumber(document.getElementById('interest_rate1').value);
            formData.remaining_years = parseInt(document.getElementById('remaining_years').value) || 0;
            formData.remaining_months = parseInt(document.getElementById('remaining_months_input').value) || 0;
            formData.extra_monthly = parseNumber(document.getElementById('extra_monthly1').value);
            formData.extra_yearly = parseNumber(document.getElementById('extra_yearly1').value);
            formData.one_time_payment = parseNumber(document.getElementById('one_time1').value);
        } else {
            formData.remaining_balance = parseNumber(document.getElementById('remaining_balance').value);
            formData.monthly_payment = parseNumber(document.getElementById('monthly_payment').value);
            formData.interest_rate = parseNumber(document.getElementById('interest_rate2').value);
            formData.extra_monthly = parseNumber(document.getElementById('extra_monthly2').value);
            formData.extra_yearly = parseNumber(document.getElementById('extra_yearly2').value);
            formData.one_time_payment = parseNumber(document.getElementById('one_time2').value);
        }
        
        try {
            const response = await fetch(window.location.href, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (!data.success) {
                document.getElementById('errorMessage').textContent = data.error;
                showState(errorState);
                return;
            }
            
            // Update results
            document.getElementById('payoffTime').textContent = data.payoff.time_string;
            document.getElementById('payoffDate').textContent = data.payoff.payoff_date;
            
            document.getElementById('interestSaved').textContent = formatCurrency(data.savings.interest_saved);
            document.getElementById('originalInterest').textContent = formatCurrency(data.original.total_interest);
            document.getElementById('payoffInterest').textContent = formatCurrency(data.payoff.total_interest);
            document.getElementById('interestPct').textContent = `${window.djangoContext.trans_Pay_0} ${data.savings.interest_pct}% ${window.djangoContext.trans_less_1}`;
            
            document.getElementById('timeSaved').textContent = data.savings.time_saved_string;
            document.getElementById('originalTime').textContent = data.original.time_string;
            document.getElementById('payoffTimeSmall').textContent = data.payoff.time_string;
            document.getElementById('timePct').textContent = `${window.djangoContext.trans_Payoff_2} ${data.savings.time_pct}% ${window.djangoContext.trans_faster_3}`;
            
            document.getElementById('tblOrigPayment').textContent = formatCurrency(data.original.monthly_payment);
            document.getElementById('tblPayoffPayment').textContent = formatCurrency(data.payoff.monthly_payment);
            document.getElementById('tblOrigTotal').textContent = formatCurrency(data.original.total_payments);
            document.getElementById('tblPayoffTotal').textContent = formatCurrency(data.payoff.total_payments);
            document.getElementById('tblOrigInterest').textContent = formatCurrency(data.original.total_interest);
            document.getElementById('tblPayoffInterestAmt').textContent = formatCurrency(data.payoff.total_interest);
            document.getElementById('tblOrigTerm').textContent = data.original.time_string;
            document.getElementById('tblPayoffTerm').textContent = data.payoff.time_string;
            
            document.getElementById('scenariosBody').innerHTML = data.scenarios.map(s => `
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-sm font-medium text-gray-900">${s.extra === 'biweekly' ? ${window.djangoContext.trans_Biweekly_4} : formatCurrency(s.extra)}</td>
                    <td class="px-4 py-3 text-sm text-gray-600 text-right">${s.payoff_time}</td>
                    <td class="px-4 py-3 text-sm text-purple-600 text-right font-medium">${s.time_saved}</td>
                    <td class="px-4 py-3 text-sm text-green-600 text-right font-medium">${formatCurrency(s.interest_saved)}</td>
                </tr>
            `).join('');
            
            document.getElementById('scheduleBody').innerHTML = data.schedule.map(row => `
                <tr class="hover:bg-gray-50">
                    <td class="px-3 py-3 text-xs text-gray-500">${row.month}</td>
                    <td class="px-3 py-3 text-xs text-gray-900">${row.date}</td>
                    <td class="px-3 py-3 text-xs text-gray-900 text-right">${formatCurrency(row.payment)}</td>
                    <td class="px-3 py-3 text-xs text-green-600 text-right">${formatCurrency(row.principal + row.extra)}</td>
                    <td class="px-3 py-3 text-xs text-red-600 text-right">${formatCurrency(row.interest)}</td>
                    <td class="px-3 py-3 text-xs text-gray-900 text-right font-medium">${formatCurrency(row.balance)}</td>
                </tr>
            `).join('');
            
            showState(resultsState);
            
            if (window.innerWidth < 1280) resultsState.scrollIntoView({ behavior: 'smooth' });
            
        } catch (err) {
            document.getElementById('errorMessage').textContent = window.djangoContext.trans_Anetworkerroroccurre_5;
            showState(errorState);
        }
    }
    
    form1.addEventListener('submit', (e) => handleSubmit(e, 1));
    form2.addEventListener('submit', (e) => handleSubmit(e, 2));
});
from django.shortcuts import render, get_object_or_404, redirect
from .forms import InvestmentFundForm  
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Wallet, InvestmentFund, Transactions
from investments.models import InvestorFund
from accounts.models import Investor

def create_investment_fund(request):
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        # total_balance = request.POST.get("total_balance")
        is_active = request.POST.get("is_active") == "True"  # Convert string to boolean

        # Check if the leader already has an investment fund
        if hasattr(request.user, 'leader') and hasattr(request.user.leader, 'managed_fund'):
            messages.error(request, "لا يمكنك إنشاء أكثر من صندوق استثماري.")
            return redirect("main:fund_dashboard_view")

        # Validate the inputs
        if not all([name, description]):
            messages.error(request, "الرجاء ملء جميع الحقول المطلوبة.")
            return redirect("main:fund_dashboard_view")

        # Create the investment fund
        try:
            InvestmentFund.objects.create(
                name=name,
                description=description,
                # total_balance=total_balance,
                is_active=is_active,
                leader=request.user.leader  # Link the fund to the current leader
            )
            # investor = Investor.objects.get(user=request.user)
            # InvestorFund.objects.create(
            #             fund=fund,
            #             investor=investor,
            #             amount_invested=0
            #         )
            messages.success(request, "تم إنشاء الصندوق الاستثماري بنجاح!")
        except Exception as e:
            messages.error(request, f"حدث خطأ: {e}")
        
        return redirect("main:fund_dashboard_view")
    else:
        return redirect("main:fund_dashboard_view")



def investment_fund_detail(request, pk):
    # Get the specific investment fund by primary key (pk)
    fund = get_object_or_404(InvestmentFund, pk=pk)
    # Pass the fund object to the template
    return render(request, 'investment_fund/detail.html', {'fund': fund})

def investment_fund_list(request):
    funds = InvestmentFund.objects.all()
    return render(request, 'investment_fund/list.html', {'funds': funds})

@login_required
def update_investment_fund(request, pk):
    fund = get_object_or_404(InvestmentFund, pk=pk)  

    if request.method == "POST":
        form = InvestmentFundForm(request.POST, instance=fund)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث الصندوق "{fund.name}" بنجاح.')
            return redirect('main:fund_dashboard_view')  # Redirect after successful update
        else:
            # Print form errors to console for debugging
            print("Form errors:", form.errors)
            messages.error(request, "يوجد خطأ في البيانات، يرجى تصحيحها.")
    else:
        form = InvestmentFundForm(instance=fund)  # Pre-fill the form with existing data

    return render(request, 'investment_fund/update.html', {
        'form': form,
        'fund': fund  
    })



def delete_investment_fund(request, pk):
    fund = get_object_or_404(InvestmentFund, pk=pk)
    if request.method == "POST":
        fund.delete()
        messages.success(request, "تم حذف الصندوق بنجاح.")
        return redirect('main:fund_dashboard_view')
    return redirect('main:fund_dashboard_view')

#------------------------------------------ Wallet login 
@login_required
def wallet_view(request):
    try:
        # Fetch the wallet for the logged-in user
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        # If the wallet doesn't exist, create one automatically
        wallet = Wallet.objects.create(user=request.user)
        messages.info(request, "تم إنشاء محفظة جديدة لك.")
    context = {
        'wallet': wallet,
    }
    return render(request, 'investment_fund/wallet_detail.html', context)
#----------------------------------------------------- Transaction logic 

@login_required
def deposit_to_wallet(request):
    if request.method == 'POST':
        try:
            # 1. Retrieve and validate amount from the form
            amount = float(request.POST.get('amount', 0))
            description = request.POST.get('description', '')

            if amount <= 0:
                messages.error(request, "المبلغ يجب أن يكون أكبر من 0.")
                return redirect('investment_fund:wallet_view')

            # 2. Get or create the user's wallet
            wallet, _ = Wallet.objects.get_or_create(user=request.user)

            # 3. Handle cases where the user doesn't have a leader or fund
            leader = getattr(request.user, 'leader', None)
            if leader:
                fund = InvestmentFund.objects.filter(leader=leader).first()
            else:
                # If user doesn't have a leader, default to a shared fund
                fund = InvestmentFund.objects.filter(name="صندوق افتراضي").first()
                if not fund:
                    fund = InvestmentFund.objects.create(
                        name="صندوق افتراضي",
                        description="صندوق مشترك لجميع المستخدمين بدون قائد",
                        leader=None,  # Optional
                        total_balance=0.0,
                        is_active='Active'
                    )

            # 4. Update wallet balance
            wallet.balance += amount
            wallet.save()

            # 5. Log the transaction
            Transactions.objects.create(
                wallet=wallet,
                fund=fund,
                transaction_type="Deposit",
                amount=amount,
                description=description,
                created_at=timezone.now()
            )

            # 6. Success message and redirect
            messages.success(request, f"تم إيداع {amount} ريال إلى محفظتك.")
            return redirect('investment_fund:wallet_view')

        except ValueError:
            # Handle invalid input
            messages.error(request, "الرجاء إدخال مبلغ صالح.")
            return redirect('investment_fund:wallet_view')
    return render(request, 'main/investor_dashboard.html')

from decimal import Decimal 
@login_required
def transfer_to_fund(request, pk):
    """Transfer money from the user's wallet to the investment fund."""
    fund = get_object_or_404(InvestmentFund, id=pk)
    wallet = Wallet.objects.get(user=request.user)

    if request.method == 'POST':
        try:
            # Validate input
            amount = Decimal(request.POST.get('amount', '0'))  # Convert to Decimal
            description = request.POST.get('description', '')

            if amount <= 0:
                messages.error(request, "المبلغ يجب أن يكون أكبر من 0.")
            elif wallet.balance < float(amount):  # Compare wallet balance with float version
                messages.error(request, "ليس لديك رصيد كافي في المحفظة.")
            else:
                # Deduct from wallet
                wallet.balance -= float(amount)  # Convert Decimal to float for wallet
                wallet.save()

                # Add to fund's total balance
                fund.total_balance += float(amount)  # Ensure consistent type
                fund.save()

                # Update or create an InvestorFund instance
                investor_fund, created = InvestorFund.objects.get_or_create(
                    investor=request.user.investor,
                    fund=fund
                )
                investor_fund.amount_invested += amount  # Decimal addition
                investor_fund.save()

                # Log the transaction
                Transactions.objects.create(
                    wallet=wallet,
                    fund=fund,
                    transaction_type="Transfer",
                    amount=float(amount),  # Log as float
                    description=description or f"Transfer to {fund.name}",
                    created_at=timezone.now()
                )

                # Success message
                messages.success(request, f"تم تحويل {amount} ريال إلى الصندوق: {fund.name}.")
                return redirect('main:investor_dashboard_view')
        
        except ValueError:
            messages.error(request, "الرجاء إدخال مبلغ صالح.")
    
    return render(request, 'main/investor_dashboard.html', {"fund": fund})

@login_required
def withdraw_profit(request):
    wallet = Wallet.objects.get(user=request.user)
    if wallet.profit_balance <= 0:
        messages.error(request, "لا يوجد رصيد أرباح كافي للسحب.")
        return redirect('investment_fund:wallet_view')

    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))

            if amount <= 0 or amount > wallet.profit_balance:
                messages.error(request, "المبلغ غير صالح أو يتجاوز الرصيد المتاح للأرباح.")
            else:
                wallet.balance += amount  # Transfer profit to the wallet balance
                wallet.profit_balance -= amount  # Deduct from profit balance
                wallet.save()

                # Log the transaction
                Transactions.objects.create(
                    wallet=wallet,
                    transaction_type="Profit Withdrawal",
                    amount=amount,
                    description="Profit Withdrawal to Wallet",
                    created_at=timezone.now()
                )

                messages.success(request, f"تم سحب {amount} ريال من الأرباح إلى محفظتك.")
                return redirect('investment_fund:wallet_view')

        except ValueError:
            messages.error(request, "الرجاء إدخال مبلغ صالح.")

    return render(request, 'main/investor_dashboard.html', {"wallet": wallet})

#-------------------------------------------------- Profit Calculate

@login_required
def investor_profit_view(request):
    # Fetch all funds the investor has invested in
    investor_funds = InvestorFund.objects.filter(investor__user=request.user)

    # Prepare data with calculated profits
    profit_data = []
    for investor_fund in investor_funds:
        profit = investor_fund.calculate_profit()
        profit_data.append({
            "fund_name": investor_fund.fund.name,
            "amount_invested": investor_fund.amount_invested,
            "profit": profit,
            "status": investor_fund.status,
        })

    context = {
        "profit_data": profit_data,
    }
    return render(request, "dashboard/investor_dashboard.html", context)



@login_required
def withdraw_profit(request):
    if request.method == "POST":
        fund_name = request.POST.get("fund_name")
        profit = float(request.POST.get("profit", 0.0))

        # Fetch the user's wallet
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet.balance += profit
        wallet.save()

        messages.success(request, f"تم سحب {profit} ريال من أرباح {fund_name} إلى محفظتك.")
        return redirect("investment_fund:investor_profit_view")

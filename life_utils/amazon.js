function emptyCart() {
	var query = document.querySelectorAll("#sc-active-cart input[value=Delete]")
	if (query.length) {
		query[0].click();
	}
	if (query.length > 1) {
		setTimeout(emptyCart,100);
	}
	else {
		console.log('Finished');
	}
}
emptyCart();


function moveWishlistToCart() {
	var query = document.querySelectorAll("#wl-item-view span[data-action='add-to-cart'] a")
	if (query.length) {
		query[0].click();
	}
	if (query.length > 1) {
		setTimeout(moveWishlistToCart,100);
	}
	else {
		console.log('Finished');
	}
}
moveWishlistToCart();


function WishlistSumPrices() {
	var priceSpans = document.querySelectorAll("#wl-item-view .a-price .a-offscreen")
	var totalSum = 0;
	priceSpans.forEach(priceSpan => {
	            var price = parseFloat(priceSpan.textContent.replace('$', ''));
	            totalSum += price;
    	});
	    
	console.log('Total sum of all prices: $' + totalSum.toFixed(2));
}
WishlistSumPrices();

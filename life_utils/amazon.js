function deleteSavedItems() {
	var query = document.querySelectorAll("#sc-active-cart input[value=Delete]")
	if (query.length) {
		query[0].click();
	}
	if (query.length > 1) {
		setTimeout(deleteSavedItems,100);
	}
	else {
		console.log('Finished');
	}
}
deleteSavedItems();


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

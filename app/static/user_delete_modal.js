'use strict';

function modalShownRecord(event) {
    let button = event.relatedTarget;
    let bookId = button.dataset.bookId;
    let newUrl = `/${bookId}/delete`;
    let form = document.getElementById('deleteModalRecordForm');
    form.action = newUrl;
}

document.addEventListener('DOMContentLoaded', function() {
    const deleteModal = document.getElementById('deleteModalBook');
    deleteModal.addEventListener('show.bs.modal', function(event) {
      const button = event.relatedTarget;
      const bookId = button.getAttribute('data-book-id');
      const form = document.getElementById('deleteModalBookForm');
      form.action = `/books/${bookId}/delete_book`;
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const deleteModal = document.getElementById('deleteModalUser');
    deleteModal.addEventListener('show.bs.modal', function(event) {
      const button = event.relatedTarget;
      const userId = button.getAttribute('data-user-id');
      const form = document.getElementById('deleteModalUserForm');
      form.action = `/users/${userId}/delete_user`;
    });
});

let modalRecord = document.getElementById('deleteModalRecord');
modalRecord.addEventListener('show.bs.modal', modalShownRecord);
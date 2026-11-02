import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from authentication.models import User
from patients.models import Patient


@pytest.mark.django_db
def test_document_upload_download_and_ownership(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    owner = User.objects.create_user(username='doc-owner', role='PATIENT')
    other = User.objects.create_user(username='doc-other', role='PATIENT')
    Patient.objects.create(user=owner)
    Patient.objects.create(user=other)
    client = APIClient()
    client.force_authenticate(owner)
    url = reverse('document-upload')
    invalid = client.post(url, {'document_type': 'OTHER', 'file': SimpleUploadedFile('bad.exe', b'bad')}, format='multipart')
    assert invalid.status_code == 400
    uploaded = client.post(url, {'document_type': 'OTHER', 'file': SimpleUploadedFile('report.pdf', b'private document')}, format='multipart')
    assert uploaded.status_code == 201
    download_url = reverse('document-download', kwargs={'pk': uploaded.data['id']})
    client.force_authenticate(other)
    assert client.get(download_url).status_code == 404
    client.force_authenticate(owner)
    result = client.get(download_url)
    assert result.status_code == 200
    assert result.content == b'private document'

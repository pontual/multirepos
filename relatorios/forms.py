from django import forms


class UploadExcelForm(forms.Form):
    file = forms.FileField(widget=forms.ClearableFileInput(attrs={'autofocus': 'autofocus'}))

class UploadTwoExcelsForm(forms.Form):
    file1 = forms.FileField()
    file2 = forms.FileField()


class PreliminaryReportForm(forms.Form):
    codigos = forms.CharField(widget=forms.Textarea, required=False)

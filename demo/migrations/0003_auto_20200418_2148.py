# Generated by Django 3.0.5 on 2020-04-18 21:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('demo', '0002_demo_competing'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='skill_level',
            field=models.CharField(choices=[('beg', 'Beginner'), ('int', 'Intermediate'), ('adv', 'Advanced')], default='beg', max_length=3),
        ),
        migrations.AddField(
            model_name='playingadmin',
            name='skill_level',
            field=models.CharField(choices=[('beg', 'Beginner'), ('int', 'Intermediate'), ('adv', 'Advanced')], default='beg', max_length=3),
        ),
        migrations.AlterField(
            model_name='demo',
            name='state',
            field=models.CharField(choices=[('wait', 'Wait'), ('play', 'Play'), ('index', 'Index'), ('over', 'Over')], default='wait', max_length=7),
        ),
    ]

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from django.shortcuts import get_object_or_404
from .models import User, Profile, Asset, IsraelPaper, USPaper, Crypto, \
    Portfolio, PortfolioComparison
from .serializers import AssetSerializer, PortfolioComparisonRetrieveSerializer, PortfolioComparisonListSerializer,\
    PortfolioCreateSerializer, \
    PortfolioListSerializer, PortfolioRetrieveSerializer, ProfileUpdateSerializer, UserSerializer,\
    PortfolioComparisonCreateSerializer
from .permissions import IsPortfolioComparisonOwner, IsPortfolioOwner


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    http_method_names = ["get", "patch"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.all()

    def list(self, request):
        serializer = self.serializer_class(
            self.get_queryset(), many=True)

        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        profile = Profile.objects.get(user__id=self.request.user.id)
        serializer = ProfileUpdateSerializer(
            profile, data=request.data, partial=True)
        serializer.is_valid()
        self.perform_update(serializer)
        return Response({"status": "Profile has been updated."}, status=status.HTTP_200_OK)


class AssetViewSet(viewsets.ViewSet):
    serializer_class = AssetSerializer
    http_method_names = ["get"]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        asset_type = self.request.query_params.get('type')
        symbol = self.request.query_params.get('symbol')
        if asset_type is not None:
            if asset_type == 'isr':
                if symbol:
                    symbol = symbol.upper()
                    try:
                        return IsraelPaper.objects.filter(paper_id=symbol)
                    except:
                        return Response({'error': 'No Israeli papers were found.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return IsraelPaper.objects.all()
            elif asset_type == 'us':
                if symbol:
                    symbol = symbol.upper()
                    try:
                        return USPaper.objects.filter(symbol=symbol)
                    except:
                        return Response({'error': 'No US papers were found.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return USPaper.objects.all()
            elif asset_type == 'crypto':
                if symbol:
                    symbol = symbol.upper()
                    try:
                        return Crypto.objects.filter(symbol=symbol)
                    except:
                        return Response({'error': 'No cryptos were found.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Crypto.objects.all()
        else:
            return Asset.objects.select_subclasses()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(
            queryset, many=True, context={'count': queryset.count()})

        if len(serializer.data) == 0:
            return Response({'error': 'No asset matching the query was found.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Asset.objects.select_subclasses()
        paper = get_object_or_404(queryset, pk=pk)
        serializer = self.serializer_class(paper, context={'count': 1})
        return Response(serializer.data)


class PortfolioViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [permissions.IsAuthenticated, IsPortfolioOwner]

    def get_queryset(self):
        return Portfolio.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return PortfolioCreateSerializer
        elif self.action in ['list', 'me']:
            return PortfolioListSerializer
        elif self.action == 'compare':
            return PortfolioComparisonCreateSerializer
        return PortfolioRetrieveSerializer

    def list(self, request):
        queryset = self.get_queryset().exclude(profile=None)
        serializer = self.get_serializer_class()(
            queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer_class()(data=request.data, context={
            'profile': self.request.user.profile, 'action': self.action})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)

    def perform_create(self, serializer):
        return serializer.save()

    def partial_update(self, request, pk=None):
        instance = Portfolio.objects.get(pk=pk)
        serializer = self.get_serializer_class()(
            instance, data=request.data, partial=True,  context={
                'profile': self.request.user.profile, 'action': self.action})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Returns the current authenticated user's portfolios
        """
        queryset = self.get_queryset().filter(profile=self.request.user.profile)
        serializer = self.get_serializer_class()(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def compare(self, request, pk=None):
        """
        Creates and returns a new PortfolioComparison object
        after generating a new portfolio using the asset provided
        """
        portfolio = self.get_object()
        try:
            asset = Asset.objects.get(id=request.data['asset'])
            portfolio_comparison = PortfolioComparison.objects.get(
                portfolio=portfolio, asset=asset)

        except:
            serializer = self.get_serializer_class()(
                data=request.data, context={'portfolio': portfolio, 'profile': request.user.profile})
            serializer.is_valid(raise_exception=True)
            portfolio_comparison = serializer.save()

        # serializer = PortfolioComparisonRetrieveSerializer(
        #     portfolio_comparison, context={'count': 1})
        serializer = PortfolioRetrieveSerializer(
            portfolio_comparison.asset_portfolio)
        return Response(serializer.data)


class PortfolioComparisonViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "delete"]
    permission_classes = [
        permissions.IsAuthenticated, IsPortfolioComparisonOwner]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PortfolioComparisonRetrieveSerializer
        return PortfolioComparisonListSerializer

    def get_queryset(self):
        # comparisons = self.request.user.profile.portfolio_comparisons
        # return comparisons
        return PortfolioComparison.objects.all()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer_class()(
            queryset, many=True, context={'count': 1})

        return Response(serializer.data)

    def destroy(self, request, pk=None):
        # Deletes asset_portfolio too
        comparison = self.get_object()
        asset_portfolio = comparison.asset_portfolio
        asset_portfolio.delete()
        comparison.delete()
        return Response({'message': 'Successfuly delete the portfolio comparison.'})
